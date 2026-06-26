"""
统一购物车存储 - Web 与 App 共用同一份数据。

购物车必须跨 Gunicorn worker、Docker 容器重启和 App/Web 请求共享，因此不能使用
Django 默认的本地内存缓存。这里使用数据库表 cart_item 按 customer_id 持久化。

数据结构：{ "isbn": {"quantity": n}, ... }
"""
from __future__ import annotations

from django.db import OperationalError, ProgrammingError, connection, transaction

from .models import CartItem


_CART_TABLE_READY = False


def _ensure_cart_table() -> None:
    """Create cart_item lazily when migrations have not been run yet."""
    global _CART_TABLE_READY
    if _CART_TABLE_READY:
        return

    table_name = CartItem._meta.db_table
    if table_name in connection.introspection.table_names():
        _CART_TABLE_READY = True
        return

    with connection.schema_editor() as schema_editor:
        if table_name not in connection.introspection.table_names():
            schema_editor.create_model(CartItem)
    _CART_TABLE_READY = True


def _with_cart_table_retry(operation):
    try:
        _ensure_cart_table()
        return operation()
    except (OperationalError, ProgrammingError):
        global _CART_TABLE_READY
        _CART_TABLE_READY = False
        _ensure_cart_table()
        return operation()


def get_cart(customer_id: int) -> dict:
    """读取某个顾客的购物车。"""
    customer_id = int(customer_id)

    def operation():
        items = CartItem.objects.filter(customer_id=customer_id).values("isbn", "quantity")
        return {
            item["isbn"]: {"quantity": int(item["quantity"])}
            for item in items
            if int(item["quantity"]) > 0
        }

    return _with_cart_table_retry(operation)


def save_cart(customer_id: int, cart: dict) -> None:
    """保存购物车，覆盖该顾客旧购物车。"""
    customer_id = int(customer_id)
    rows = []
    for isbn, data in (cart or {}).items():
        try:
            quantity = int(data.get("quantity", 0))
        except (AttributeError, TypeError, ValueError):
            quantity = 0
        if quantity > 0:
            rows.append(CartItem(customer_id=customer_id, isbn=str(isbn), quantity=quantity))

    def operation():
        with transaction.atomic():
            CartItem.objects.filter(customer_id=customer_id).delete()
            if rows:
                CartItem.objects.bulk_create(rows)

    _with_cart_table_retry(operation)


def clear_cart(customer_id: int) -> None:
    """清空购物车（支付成功后调用）。"""
    customer_id = int(customer_id)

    def operation():
        CartItem.objects.filter(customer_id=customer_id).delete()

    _with_cart_table_retry(operation)
