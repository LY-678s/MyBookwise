"""
序列化：将 Model / 业务数据转为 JSON。

图书封面逻辑与 views.get_book_cover_image / index 保持一致。
"""
from __future__ import annotations

import base64
import re
from decimal import Decimal

from django.conf import settings
from urllib.parse import quote

from bookstore.models import Book, Bookauthor, Customer, Orderdetail, Orders


def _static_cover_url(filename: str) -> str:
    prefix = settings.STATIC_URL if settings.STATIC_URL.endswith("/") else settings.STATIC_URL + "/"
    subdir = getattr(settings, "COVER_IMAGE_SUBDIR", "images")
    return f"{prefix}{subdir}/{quote(filename)}"


def _cover_url_for_title(title: str) -> str | None:
    """复用 Web 端书名→静态封面映射（settings.COVER_IMAGE_MAPPINGS）。"""
    title_lower = title.lower()
    for keyword, filename in getattr(settings, "COVER_IMAGE_MAPPINGS", {}).items():
        if keyword in title_lower:
            return _static_cover_url(filename)
    return None


def _cover_base64(raw) -> str | None:
    """将数据库 CoverImage 字段转为 base64 字符串（与 views.index 逻辑一致）。"""
    if not raw:
        return None
    try:
        if isinstance(raw, str):
            s = raw.strip()
            if re.fullmatch(r"[A-Za-z0-9+/=\s]+", s) and len(s) > 50:
                return s.replace("\\n", "").replace("\\r", "")
            return base64.b64encode(s.encode("utf-8")).decode("utf-8")
        return base64.b64encode(raw).decode("utf-8")
    except Exception:
        return None


def serialize_book(book: Book, *, include_authors: bool = False) -> dict:
    """图书 JSON；对应 Web index / book_detail。"""
    from bookstore.views import _build_book_data, app_cover_url

    built = _build_book_data(book)
    data = {
        "isbn": built["isbn"],
        "title": built["title"],
        "publisher": built["publisher"],
        "price": str(built["price"]),
        "keywords": built["keywords"],
        "stockqty": built["stockqty"],
        "location": built["location"],
        "minstocklimit": built["minstocklimit"],
        "cover_image_url": app_cover_url(built["isbn"]),
        "coverimage": None,
    }
    if include_authors:
        authors = (
            Bookauthor.objects.filter(isbn=book)
            .order_by("authororder")
            .values_list("authorname", flat=True)
        )
        data["authors"] = list(authors)
    return data


def default_cover_url() -> str:
    filename = getattr(settings, "DEFAULT_COVER_IMAGE_FILENAME", "default_cover.png")
    return _static_cover_url(filename)


def serialize_customer(customer: Customer, *, include_private: bool = True) -> dict:
    """顾客信息 JSON。"""
    from bookstore.membership import get_display_member_level, get_purchase_discount_rate, is_member

    level = customer.levelid
    member = is_member(customer.customerid)
    rate = get_purchase_discount_rate(customer.customerid)
    discount_percent = (Decimal("1") - rate) * 100
    display_level = get_display_member_level(customer.customerid)

    data = {
        "customerid": customer.customerid,
        "username": customer.username,
        "name": customer.name,
        "email": customer.email,
        "address": customer.address,
        "levelid": display_level,
        "discount_rate": str(rate),
        "discount_percent": str(discount_percent.quantize(Decimal("0.01"))),
        "registerdate": customer.registerdate.isoformat() if customer.registerdate else None,
    }
    if not include_private:
        data.pop("username", None)
    return data


def serialize_account_summary(customer: Customer) -> dict:
    """会员页完整摘要。"""
    from bookstore.membership import serialize_membership

    data = serialize_customer(customer)
    data.update(serialize_membership(customer.customerid))
    return data


def serialize_order_detail_line(detail: Orderdetail, discount_rate: Decimal) -> dict:
    original = detail.quantity * detail.unitprice
    discounted = original * discount_rate
    return {
        "detailid": detail.detailid,
        "isbn": detail.isbn_id,
        "title": detail.isbn.title,
        "quantity": detail.quantity,
        "unitprice": str(detail.unitprice),
        "isshipped": detail.isshipped,
        "original_amount": str(original),
        "discounted_amount": str(discounted),
    }


def _normalize_payment_status(paymentstatus: int) -> int:
    """对外仅 0=未付、1=已付、3=已退款。"""
    return paymentstatus


def serialize_order(order: Orders, *, customer: Customer | None = None) -> dict:
    """订单 JSON；customer 传入时附带明细与折扣信息。"""
    details = Orderdetail.objects.filter(orderid=order).select_related("isbn")
    original_amount = sum(d.quantity * d.unitprice for d in details)
    total = order.totalamount or Decimal("0")
    payment_status = _normalize_payment_status(order.paymentstatus)
    actual_paid = order.actualpaid or Decimal("0")
    if payment_status == 1:
        unpaid = Decimal("0")
    else:
        unpaid = max(total - actual_paid, Decimal("0"))

    data = {
        "orderid": order.orderid,
        "orderno": order.orderno,
        "orderdate": order.orderdate.isoformat() if order.orderdate else None,
        "shipaddress": order.shipaddress,
        "totalamount": str(total),
        "actualpaid": str(actual_paid),
        "unpaid_amount": str(unpaid),
        "paymentstatus": payment_status,
        "status": order.status,
        "original_amount": str(original_amount),
        "discount_amount": str(original_amount - total),
    }

    if customer is not None:
        from bookstore.membership import get_purchase_discount_rate

        rate = get_purchase_discount_rate(customer.customerid)
        data["details"] = [serialize_order_detail_line(d, rate) for d in details]
        data["discount_rate"] = str(rate)
        data["discount_percent"] = str(((Decimal("1") - rate) * 100).quantize(Decimal("0.01")))

    return data
