"""Stripe Test Mode：订单购书、畅读卡 Checkout。"""
from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

from .membership import activate_reading_pass, is_member
from .models import Customer, Orders, StripePaymentRecord


class StripeServiceError(Exception):
    pass


def is_stripe_configured() -> bool:
    return bool(getattr(settings, "STRIPE_SECRET_KEY", "").strip())


def _stripe():
    if not is_stripe_configured():
        raise StripeServiceError("在线支付暂不可用，请联系管理员。")
    import stripe

    stripe.api_key = settings.STRIPE_SECRET_KEY.strip()
    return stripe


def _require_email(customer: Customer) -> str:
    email = (customer.email or "").strip()
    if not email:
        raise StripeServiceError("请先在「基本信息」中填写邮箱。")
    return email


def create_order_checkout(
    customer: Customer,
    order: Orders,
    success_url: str,
    cancel_url: str,
) -> tuple[str, str]:
    """创建图书订单 Stripe Checkout 会话。"""
    stripe = _stripe()
    amount = order.totalamount or Decimal("0")
    amount_cents = int(amount * 100)
    if amount_cents < 1:
        raise StripeServiceError("订单金额无效")

    email = _require_email(customer)

    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card", "alipay"],
        line_items=[
            {
                "price_data": {
                    "currency": "cny",
                    "unit_amount": amount_cents,
                    "product_data": {
                        "name": f"MyBookwise 订单 {order.orderno}",
                        "description": "图书订单",
                    },
                },
                "quantity": 1,
            }
        ],
        metadata={
            "customer_id": str(customer.customerid),
            "purpose": "order",
            "order_id": str(order.orderid),
        },
        success_url=success_url,
        cancel_url=cancel_url,
        customer_email=email,
    )

    StripePaymentRecord.objects.create(
        customer=customer,
        session_id=session.id,
        amount_cents=amount_cents,
        currency="cny",
        purpose="order",
        status="pending",
    )
    return session.url, session.id


def create_reading_pass_checkout(customer: Customer, success_url: str, cancel_url: str) -> tuple[str, str]:
    if not is_member(customer.customerid):
        raise StripeServiceError("请先免费开通会员，再购买畅读卡。")

    stripe = _stripe()
    amount_cents = int(getattr(settings, "STRIPE_READING_PASS_AMOUNT_CENTS", 2000))
    email = _require_email(customer)

    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card", "alipay"],
        line_items=[
            {
                "price_data": {
                    "currency": "cny",
                    "unit_amount": amount_cents,
                    "product_data": {
                        "name": "MyBookwise 畅读卡（30天）",
                        "description": "等级折扣 × 7.2 折购书",
                    },
                },
                "quantity": 1,
            }
        ],
        metadata={
            "customer_id": str(customer.customerid),
            "purpose": "reading_pass",
        },
        success_url=success_url,
        cancel_url=cancel_url,
        customer_email=email,
    )

    StripePaymentRecord.objects.create(
        customer=customer,
        session_id=session.id,
        amount_cents=amount_cents,
        currency="cny",
        purpose="reading_pass",
        status="pending",
    )
    return session.url, session.id


create_membership_checkout = create_reading_pass_checkout


def _fulfill_order_payment(record: StripePaymentRecord, session) -> tuple[bool, dict]:
    from .cart_store import clear_cart
    from .membership import is_member, serialize_membership
    from .signals import complete_order_payment

    order_id = (session.metadata or {}).get("order_id")
    if not order_id:
        return False, {"error": "支付记录缺少订单信息。"}

    try:
        order = Orders.objects.get(pk=int(order_id), customerid=record.customer_id)
    except (Orders.DoesNotExist, ValueError, TypeError):
        return False, {"error": "订单不存在。"}

    if order.paymentstatus == 1:
        return True, {
            "message": "订单已支付",
            "already_fulfilled": True,
            "order_id": order.orderid,
        }

    customer = Customer.objects.select_related("levelid").get(pk=record.customer_id)
    try:
        msg = complete_order_payment(order, customer)
    except ValidationError as exc:
        return False, {"error": str(exc.message if hasattr(exc, "message") else exc)}
    clear_cart(record.customer_id)

    record.status = "paid"
    record.paid_at = timezone.now()
    record.save(update_fields=["status", "paid_at"])

    result = {
        "message": msg,
        "order_id": order.orderid,
    }
    if is_member(customer.customerid):
        result["membership"] = serialize_membership(customer.customerid)
    return True, result


def fulfill_checkout_session(session_id: str) -> tuple[bool, dict]:
    stripe = _stripe()
    session = stripe.checkout.Session.retrieve(session_id)

    if session.payment_status != "paid":
        return False, {"error": "支付尚未完成，请稍后再试。"}

    record = StripePaymentRecord.objects.filter(session_id=session_id).first()
    if not record:
        return False, {"error": "未找到支付记录。"}

    if record.status == "paid":
        from .membership import serialize_membership

        purpose = record.purpose
        if purpose == "order":
            order_id = (session.metadata or {}).get("order_id")
            return True, {
                "message": "订单已支付",
                "already_fulfilled": True,
                "order_id": int(order_id) if order_id else None,
            }
        return True, {
            "message": "畅读卡已生效",
            "already_fulfilled": True,
            "membership": serialize_membership(record.customer_id),
        }

    meta_customer_id = (session.metadata or {}).get("customer_id")
    if meta_customer_id and str(record.customer_id) != str(meta_customer_id):
        return False, {"error": "支付记录与用户不匹配。"}

    purpose = (session.metadata or {}).get("purpose") or record.purpose
    if purpose == "order":
        return _fulfill_order_payment(record, session)

    if purpose == "reading_pass":
        activate_reading_pass(record.customer_id)
        record.status = "paid"
        record.paid_at = timezone.now()
        record.save(update_fields=["status", "paid_at"])
        from .membership import serialize_membership

        return True, {
            "message": "畅读卡开通成功！30 天内享等级折扣 × 7.2 折购书。",
            "membership": serialize_membership(record.customer_id),
        }

    activate_reading_pass(record.customer_id)
    record.status = "paid"
    record.paid_at = timezone.now()
    record.save(update_fields=["status", "paid_at"])
    return True, {"message": "处理完成"}


def handle_webhook_payload(payload: bytes, sig_header: str) -> tuple[bool, dict]:
    stripe = _stripe()
    secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "").strip()
    if not secret:
        raise StripeServiceError("尚未配置 STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, secret)
    except Exception as exc:
        raise StripeServiceError(f"Webhook 验签失败：{exc}") from exc

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        ok, result = fulfill_checkout_session(session["id"])
        return ok, result

    return True, {"message": "ignored"}
