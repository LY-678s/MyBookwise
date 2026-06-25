"""
API 业务服务层：复用 Web views.py 中的核心逻辑，避免 APP 端重复实现规则。

购物车与 Web 共用 bookstore.cart_store（按 customer_id 存 Cache）。
"""
from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.db.models import F, Q, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone

from bookstore.cart_store import clear_cart, get_cart, save_cart
from bookstore.models import Book, Creditlevel, Customer, Orderdetail, Orders

from .serializers import serialize_book, serialize_customer, serialize_order


# ---------------------------------------------------------------------------
# 购物车（对应 views._get_cart / cart_*，存储见 cart_store.py）
# ---------------------------------------------------------------------------


def add_to_cart(customer_id: int, isbn: str, quantity: int = 1) -> dict:
    """对应 views.cart_add。"""
    book = get_object_or_404(Book, pk=isbn)
    if quantity < 1:
        quantity = 1
    cart = get_cart(customer_id)
    item = cart.get(isbn, {"quantity": 0})
    item["quantity"] += quantity
    cart[isbn] = item
    save_cart(customer_id, cart)
    return {"message": f"已将《{book.title}》× {quantity} 加入购物车", "cart": build_cart_payload(customer_id)}


def update_cart_item(customer_id: int, isbn: str, quantity: int) -> dict:
    """对应 views.cart_update。"""
    cart = get_cart(customer_id)
    if quantity > 0:
        cart[isbn] = {"quantity": quantity}
        message = "购物车已更新"
    else:
        cart.pop(isbn, None)
        message = "已从购物车移除"
    save_cart(customer_id, cart)
    return {"message": message, "cart": build_cart_payload(customer_id)}


def remove_from_cart(customer_id: int, isbn: str) -> dict:
    """对应 views.cart_remove。"""
    cart = get_cart(customer_id)
    cart.pop(isbn, None)
    save_cart(customer_id, cart)
    return {"message": "已从购物车移除", "cart": build_cart_payload(customer_id)}


def build_cart_payload(customer_id: int) -> dict:
    """对应 views.cart_detail 的计算逻辑。"""
    from bookstore.membership import get_purchase_discount_rate

    customer = Customer.objects.select_related("levelid").get(pk=customer_id)
    cart = get_cart(customer_id)
    discount_rate = get_purchase_discount_rate(customer_id)
    discount_percent = (Decimal("1") - discount_rate) * 100
    items = []
    original_total = Decimal("0")

    for isbn, data in cart.items():
        book = get_object_or_404(Book, pk=isbn)
        quantity = data["quantity"]
        original_amount = book.price * quantity
        discounted_amount = original_amount * discount_rate
        original_total += original_amount
        items.append(
            {
                "book": serialize_book(book),
                "quantity": quantity,
                "original_amount": str(original_amount),
                "discounted_amount": str(discounted_amount),
            }
        )

    discounted_total = original_total * discount_rate
    return {
        "items": items,
        "original_total": str(original_total),
        "discounted_total": str(discounted_total),
        "discount_amount": str(original_total - discounted_total),
        "discount_rate": str(discount_rate),
        "discount_percent": str(discount_percent.quantize(Decimal("0.01"))),
        "customer": serialize_customer(customer),
    }


def build_order_preview(customer_id: int) -> dict:
    """对应 views.order_confirm GET。"""
    cart = get_cart(customer_id)
    if not cart:
        return {"empty": True, "message": "购物车为空"}
    payload = build_cart_payload(customer_id)
    payload["empty"] = False
    return payload


# ---------------------------------------------------------------------------
# 订单（对应 views.order_confirm POST / order_list / order_detail 等）
# ---------------------------------------------------------------------------


def abandon_unpaid_order(customer: Customer, order_id: int) -> tuple[bool, str]:
    """取消未支付订单（支付放弃时调用，商品仍在购物车）。"""
    try:
        order = Orders.objects.get(pk=order_id, customerid=customer, paymentstatus=0)
    except Orders.DoesNotExist:
        return False, "订单不存在或已支付"
    if order.status != 4:
        order.status = 4
        order.save(update_fields=["status"])
    return True, "已取消"


def abandon_customer_pending_orders(customer_id: int) -> None:
    """作废该用户所有未支付订单（再次下单前清理）。"""
    Orders.objects.filter(
        customerid_id=customer_id,
        paymentstatus=0,
    ).exclude(status=4).update(status=4)


def _create_pending_order_from_cart(
    customer: Customer,
    *,
    shipping_name: str,
    shipping_contact: str,
    shipping_address: str,
) -> Orders:
    """从购物车创建待支付订单（不扣款、不清购物车）。"""
    from bookstore.membership import apply_reading_pass_to_order_total, get_purchase_discount_rate

    cart = get_cart(customer.customerid)
    if not cart:
        raise ValueError("购物车为空")

    customer = Customer.objects.select_for_update().select_related("levelid").get(pk=customer.customerid)
    now = timezone.now()
    date_prefix = now.strftime("%Y%m%d")
    today_count = Orders.objects.filter(orderno__startswith=date_prefix).count()
    order_number = f"{date_prefix}{today_count + 1:02d}"
    full_address = f"{shipping_name} ({shipping_contact}) - {shipping_address}"

    order = Orders.objects.create(
        orderno=order_number,
        orderdate=now,
        customerid=customer,
        shipaddress=full_address,
        totalamount=Decimal("0"),
        actualpaid=Decimal("0"),
        paymentstatus=0,
        status=0,
    )

    for isbn, data in cart.items():
        book = get_object_or_404(Book, pk=isbn)
        Orderdetail.objects.create(
            orderid=order,
            isbn=book,
            quantity=data["quantity"],
            unitprice=book.price,
            isshipped=0,
        )

    order.refresh_from_db()
    total_amount = order.totalamount or Decimal("0")
    if total_amount == 0:
        manual_total = Orderdetail.objects.filter(orderid=order).aggregate(
            total=Sum(F("quantity") * F("unitprice"))
        )["total"] or Decimal("0")
        rate = get_purchase_discount_rate(customer.customerid)
        total_amount = manual_total * rate
        order.totalamount = total_amount
        order.save(update_fields=["totalamount"])

    adjusted = apply_reading_pass_to_order_total(customer.customerid, order.totalamount or Decimal("0"))
    if adjusted != order.totalamount:
        order.totalamount = adjusted
        order.save(update_fields=["totalamount"])

    return order


def _resolve_checkout_urls(
    success_url: str | None,
    cancel_url: str | None,
    order_id: int,
    *,
    site: str,
) -> tuple[str, str]:
    """解析 App deep link 中的 {order_id} 占位符。"""
    oid = str(order_id)
    pay_success = (success_url or f"{site}/orders/{order_id}/?session_id={{CHECKOUT_SESSION_ID}}").replace(
        "{order_id}", oid
    )
    pay_cancel = (cancel_url or f"{site}/order/confirm/?canceled=1&order_id={order_id}").replace(
        "{order_id}", oid
    )
    return pay_success, pay_cancel


def create_order(
    customer: Customer,
    *,
    shipping_name: str | None = None,
    shipping_contact: str | None = None,
    shipping_address: str | None = None,
    success_url: str | None = None,
    cancel_url: str | None = None,
) -> tuple[bool, dict]:
    """
    从购物车创建订单并返回 Stripe 支付链接。
    支付完成后在 fulfill_checkout_session 中标记已付并清空购物车。
    """
    from django.conf import settings

    from bookstore.stripe_service import StripeServiceError, create_order_checkout, is_stripe_configured

    cart = get_cart(customer.customerid)
    if not cart:
        return False, {"error": "购物车为空"}

    shipping_name = (shipping_name or customer.name or "").strip()
    shipping_contact = (shipping_contact or customer.email or "").strip()
    shipping_address = (shipping_address or customer.address or "").strip()
    if not shipping_address:
        return False, {"error": "请填写发货地址"}

    if not is_stripe_configured():
        return False, {"error": "在线支付暂不可用，请联系管理员"}

    abandon_customer_pending_orders(customer.customerid)

    try:
        with transaction.atomic():
            order = _create_pending_order_from_cart(
                customer,
                shipping_name=shipping_name,
                shipping_contact=shipping_contact,
                shipping_address=shipping_address,
            )
    except ValueError as exc:
        return False, {"error": str(exc)}

    site = getattr(settings, "SITE_URL", "http://127.0.0.1:8000").rstrip("/")
    pay_success, pay_cancel = _resolve_checkout_urls(success_url, cancel_url, order.orderid, site=site)

    try:
        customer_ref = Customer.objects.select_related("levelid").get(pk=customer.customerid)
        checkout_url, _ = create_order_checkout(customer_ref, order, pay_success, pay_cancel)
    except StripeServiceError as exc:
        order.status = 4
        order.save(update_fields=["status"])
        return False, {"error": str(exc)}

    return True, {
        "message": "订单已创建，请完成支付",
        "order": serialize_order(order, customer=customer_ref),
        "checkout_url": checkout_url,
    }


def start_order_payment(
    customer: Customer,
    order_id: int,
    *,
    success_url: str | None = None,
    cancel_url: str | None = None,
) -> tuple[bool, dict]:
    """未支付订单重新发起 Stripe Checkout（App/Web 兼容，一般不再使用）。"""
    from django.conf import settings

    from bookstore.stripe_service import StripeServiceError, create_order_checkout, is_stripe_configured

    if not is_stripe_configured():
        return False, {"error": "在线支付暂不可用"}

    try:
        order = Orders.objects.get(pk=order_id, customerid=customer)
    except Orders.DoesNotExist:
        return False, {"error": "订单不存在"}

    if order.paymentstatus != 0 or order.status == 4:
        return False, {"error": "该订单无需支付"}

    site = getattr(settings, "SITE_URL", "http://127.0.0.1:8000").rstrip("/")
    pay_success, pay_cancel = _resolve_checkout_urls(success_url, cancel_url, order.orderid, site=site)

    try:
        checkout_url, _ = create_order_checkout(customer, order, pay_success, pay_cancel)
    except StripeServiceError as exc:
        return False, {"error": str(exc)}

    return True, {"message": "请完成支付", "checkout_url": checkout_url, "order": serialize_order(order, customer=customer)}


def list_orders(customer: Customer) -> list[dict]:
    """对应 views.order_list（仅展示已支付订单）。"""
    orders = (
        Orders.objects.filter(customerid=customer)
        .exclude(paymentstatus=0)
        .order_by("-orderdate")
    )
    result = []
    for order in orders:
        item = serialize_order(order)
        result.append(item)
    return result


def get_order(customer: Customer, order_id: int) -> dict | None:
    """对应 views.order_detail（未支付订单不对外展示）。"""
    try:
        order = Orders.objects.get(pk=order_id, customerid=customer)
    except Orders.DoesNotExist:
        return None
    if order.paymentstatus == 0:
        return None
    return serialize_order(order, customer=customer)


def pay_order_remainder(customer: Customer, order_id: int) -> tuple[bool, dict]:
    return False, {"error": "请重新下单并完成在线支付"}


def abandon_checkout_order(customer: Customer, order_id: int) -> tuple[bool, dict]:
    """Stripe 支付取消：作废待支付订单。"""
    ok, msg = abandon_unpaid_order(customer, order_id)
    if not ok:
        return False, {"error": msg}
    return True, {"message": "已取消支付"}


def cancel_order(customer: Customer, order_id: int) -> tuple[bool, dict]:
    """对应 views.cancel_order。"""
    try:
        order = Orders.objects.get(pk=order_id, customerid=customer)
    except Orders.DoesNotExist:
        return False, {"error": "订单不存在"}

    if order.status == 4:
        return False, {"error": "该订单已取消"}
    if order.status == 1:
        return False, {"error": "已发货的订单不能取消，请联系客服"}
    if order.status == 2:
        return False, {"error": "已完成的订单不能取消"}

    with transaction.atomic():
        order.status = 4
        order.save(update_fields=["status"])
    return True, {"message": "订单已取消", "order": serialize_order(order, customer=customer)}


def confirm_receipt(customer: Customer, order_id: int) -> tuple[bool, dict]:
    """对应 views.confirm_receipt。"""
    try:
        order = Orders.objects.get(pk=order_id, customerid=customer)
    except Orders.DoesNotExist:
        return False, {"error": "订单不存在"}

    if order.status != 1:
        return False, {"error": "只有已发货的订单才能确认收货"}

    order.status = 2
    order.save(update_fields=["status"])
    return True, {
        "message": "已确认收货，感谢您的购买！",
        "order": serialize_order(order, customer=customer),
    }


# ---------------------------------------------------------------------------
# 账户（对应 views.customer_register / account_*）
# ---------------------------------------------------------------------------

def register_customer(data: dict) -> tuple[bool, dict]:
    """对应 views.customer_register。"""
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()
    confirm = (data.get("confirm_password") or password).strip()
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    address = (data.get("address") or "").strip()

    if not all([username, password, name, email]):
        return False, {"error": "用户名、密码、姓名、邮箱为必填项"}
    if password != confirm:
        return False, {"error": "两次输入的密码不一致"}
    if len(password) < 6:
        return False, {"error": "密码长度至少6位"}
    if Customer.objects.filter(username=username).exists():
        return False, {"error": "用户名已存在"}
    if Customer.objects.filter(email=email).exists():
        return False, {"error": "邮箱已被注册"}

    customer = Customer.objects.create(
        username=username,
        password=password,
        name=name,
        email=email,
        address=address,
        levelid_id=0,
        creditlimit=Decimal("0.00"),
        usedcredit=Decimal("0.00"),
        registerdate=timezone.now(),
    )
    return True, {"customer": customer, "message": f"注册成功！欢迎加入，{customer.name}"}


def login_customer(username: str, password: str) -> tuple[bool, dict]:
    """对应 views.customer_login。"""
    try:
        customer = Customer.objects.select_related("levelid").get(username=username, password=password)
    except Customer.DoesNotExist:
        return False, {"error": "用户名或密码错误"}
    return True, {"customer": customer, "message": "登录成功"}


def update_account(customer: Customer, data: dict) -> tuple[bool, dict]:
    """对应 views.account_edit。"""
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    address = (data.get("address") or "").strip()
    current_password = data.get("current_password") or ""
    new_password = (data.get("new_password") or "").strip()
    confirm_password = (data.get("confirm_password") or "").strip()

    if not name or not email:
        return False, {"error": "姓名和邮箱不能为空"}
    if Customer.objects.filter(email=email).exclude(customerid=customer.customerid).exists():
        return False, {"error": "邮箱已被其他用户使用"}

    if new_password:
        if customer.password != current_password:
            return False, {"error": "当前密码不正确"}
        if new_password != confirm_password:
            return False, {"error": "两次输入的新密码不一致"}
        if len(new_password) < 6:
            return False, {"error": "新密码长度至少6位"}
        customer.password = new_password

    customer.name = name
    customer.email = email
    customer.address = address
    customer.save()
    return True, {"message": "账户信息更新成功", "customer": customer}


def repay_all_overdraft(customer: Customer) -> tuple[bool, dict]:
    return False, {"error": "当前不支持余额还款，取消未发货订单可释放信用额度。"}


def search_books(query: str):
    """对应 views.search。"""
    books = Book.objects.all().order_by("title")
    if query:
        books = books.filter(
            Q(title__icontains=query) | Q(keywords__icontains=query) | Q(isbn__icontains=query)
        )
    return books
