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
from bookstore.signals import _calculate_credit_level, process_payment

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
    customer = Customer.objects.select_related("levelid").get(pk=customer_id)
    cart = get_cart(customer_id)
    discount_rate = customer.levelid.discountrate
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

def create_order(
    customer: Customer,
    *,
    payment_choice: str = "balance",
    shipping_name: str | None = None,
    shipping_contact: str | None = None,
    shipping_address: str | None = None,
) -> tuple[bool, dict]:
    """
    从购物车创建订单并支付。
    对应 views.order_confirm POST；成功返回 (True, order_dict)，失败返回 (False, error_dict)。
    """
    cart = get_cart(customer.customerid)
    if not cart:
        return False, {"error": "购物车为空"}

    shipping_name = (shipping_name or customer.name or "").strip()
    shipping_contact = (shipping_contact or customer.email or "").strip()
    shipping_address = (shipping_address or customer.address or "").strip()
    if not shipping_address:
        return False, {"error": "请填写发货地址"}

    use_credit_only = payment_choice == "credit"

    with transaction.atomic():
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
            total_amount = manual_total * customer.levelid.discountrate
            order.totalamount = total_amount
            order.save(update_fields=["totalamount"])

        success, result = process_payment(order, customer, use_credit_only=use_credit_only)
        if success:
            msg, actual_paid, payment_status = result
            order.actualpaid = actual_paid
            order.paymentstatus = payment_status
            order.save(update_fields=["actualpaid", "paymentstatus"])
            clear_cart(customer.customerid)
            return True, {
                "message": f"下单成功！{msg}",
                "order": serialize_order(order, customer=customer),
            }

        order.status = 4
        order.save(update_fields=["status"])
        return False, {"error": f"下单失败：{result}。订单已取消。"}


def list_orders(customer: Customer) -> list[dict]:
    """对应 views.order_list。"""
    orders = Orders.objects.filter(customerid=customer).order_by("-orderdate")
    result = []
    for order in orders:
        item = serialize_order(order)
        result.append(item)
    return result


def get_order(customer: Customer, order_id: int) -> dict | None:
    """对应 views.order_detail。"""
    try:
        order = Orders.objects.get(pk=order_id, customerid=customer)
    except Orders.DoesNotExist:
        return None
    return serialize_order(order, customer=customer)


def pay_order_remainder(customer: Customer, order_id: int) -> tuple[bool, dict]:
    """对应 views.pay_order。"""
    try:
        order = Orders.objects.get(pk=order_id, customerid=customer)
    except Orders.DoesNotExist:
        return False, {"error": "订单不存在"}

    if order.paymentstatus == 1:
        return False, {"error": "该订单已全额支付"}
    if order.paymentstatus != 2:
        return False, {"error": "该订单不需要补足支付"}

    with transaction.atomic():
        customer = Customer.objects.select_for_update().select_related("levelid").get(pk=customer.customerid)
        order.refresh_from_db()
        unpaid = order.totalamount - order.actualpaid

        if customer.balance < unpaid:
            return False, {
                "error": f"余额不足！需要¥{unpaid}，当前余额¥{customer.balance}，请先充值"
            }

        customer.balance -= unpaid
        customer.totalspent += unpaid
        customer.usedcredit -= unpaid

        new_level_id = _calculate_credit_level(customer.totalspent)
        old_level = customer.levelid.levelid
        upgraded = new_level_id != old_level
        if upgraded:
            customer.levelid = Creditlevel.objects.get(levelid=new_level_id)

        customer.save(update_fields=["balance", "usedcredit", "totalspent", "levelid"])
        order.actualpaid = order.totalamount
        order.paymentstatus = 1
        order.save(update_fields=["actualpaid", "paymentstatus"])

        msg = f"补足支付成功！支付¥{unpaid}，当前余额¥{customer.balance}"
        if upgraded:
            msg += f"，信用等级已升级至{new_level_id}级！"
        return True, {"message": msg, "order": serialize_order(order, customer=customer)}


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
        balance=Decimal("0.00"),
        levelid_id=1,
        creditlimit=Decimal("0.00"),
        usedcredit=Decimal("0.00"),
        totalspent=Decimal("0.00"),
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


def recharge_account(customer: Customer, amount: Decimal) -> tuple[bool, dict]:
    """对应 views.account_recharge POST。"""
    if amount <= 0:
        return False, {"error": "充值金额必须大于0"}

    with transaction.atomic():
        customer = Customer.objects.select_for_update().get(pk=customer.customerid)
        customer.balance += amount
        customer.save(update_fields=["balance"])
    return True, {
        "message": f"充值成功！充值金额：¥{amount}，当前余额：¥{customer.balance}",
        "customer": customer,
    }


def repay_all_overdraft(customer: Customer) -> tuple[bool, dict]:
    """对应 views.repay_overdraft POST。"""
    with transaction.atomic():
        customer = Customer.objects.select_for_update().select_related("levelid").get(pk=customer.customerid)

        if customer.usedcredit <= 0:
            return False, {"error": "您当前没有未还款的订单"}

        if customer.balance < customer.usedcredit:
            return False, {
                "error": f"余额不足！需要¥{customer.usedcredit}，当前余额¥{customer.balance}，请先充值"
            }

        unpaid_orders = Orders.objects.filter(
            customerid=customer,
            paymentstatus=2,
            status__in=[0, 1],
        )
        total_repay = Decimal("0")
        repay_count = 0

        for order in unpaid_orders:
            unpaid_amount = order.totalamount - order.actualpaid
            customer.balance -= unpaid_amount
            customer.totalspent += unpaid_amount
            total_repay += unpaid_amount
            order.actualpaid = order.totalamount
            order.paymentstatus = 1
            order.save(update_fields=["actualpaid", "paymentstatus"])
            repay_count += 1

        customer.usedcredit = Decimal("0")
        new_level_id = _calculate_credit_level(customer.totalspent)
        old_level = customer.levelid.levelid
        upgraded = new_level_id != old_level
        if upgraded:
            customer.levelid = Creditlevel.objects.get(levelid=new_level_id)
            customer.save(update_fields=["balance", "usedcredit", "totalspent", "levelid"])
        else:
            customer.save(update_fields=["balance", "usedcredit", "totalspent"])

        msg = f"还款成功！还清了{repay_count}个订单，共¥{total_repay}，当前余额：¥{customer.balance}"
        if upgraded:
            msg += f"，信用等级已升级至{new_level_id}级！"
        return True, {"message": msg, "customer": customer}


def search_books(query: str):
    """对应 views.search。"""
    books = Book.objects.all().order_by("title")
    if query:
        books = books.filter(
            Q(title__icontains=query) | Q(keywords__icontains=query) | Q(isbn__icontains=query)
        )
    return books
