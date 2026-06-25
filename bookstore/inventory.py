"""库存校验与扣减（替代 orderdetail 插入触发器，避免 MySQL 1442）。"""
from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F

from bookstore.models import Book, Orderdetail, Orders


def validate_cart_stock(cart: dict) -> None:
    """下单前检查购物车商品库存是否充足。"""
    if not cart:
        return
    totals: dict[str, int] = {}
    for isbn, data in cart.items():
        totals[isbn] = totals.get(isbn, 0) + int(data.get("quantity") or 0)

    shortages: list[str] = []
    for isbn, qty in totals.items():
        if qty <= 0:
            continue
        book = Book.objects.get(pk=isbn)
        if book.stockqty < qty:
            shortages.append(f"《{book.title}》")
    if shortages:
        raise ValueError(f"库存不足：{', '.join(shortages)}")


def deduct_order_stock(order: Orders) -> None:
    """支付成功后扣减订单明细对应库存（与旧触发器 tr_AfterInsertOrderDetail 等价）。"""
    with transaction.atomic():
        details = Orderdetail.objects.filter(orderid=order).select_related("isbn")
        for detail in details:
            book = Book.objects.select_for_update().get(pk=detail.isbn_id)
            if book.stockqty < detail.quantity:
                raise ValidationError(
                    f"图书《{book.title}》库存不足，当前库存 {book.stockqty}，需要 {detail.quantity}。"
                )
            Book.objects.filter(pk=book.pk).update(stockqty=F("stockqty") - detail.quantity)
