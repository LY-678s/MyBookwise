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
    cover_url = _cover_url_for_title(book.title)
    data = {
        "isbn": book.isbn,
        "title": book.title,
        "publisher": book.publisher,
        "price": str(book.price),
        "keywords": book.keywords,
        "stockqty": book.stockqty,
        "location": book.location,
        "minstocklimit": book.minstocklimit,
        "cover_image_url": cover_url,
        "coverimage": None if cover_url else _cover_base64(book.coverimage),
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
    filename = getattr(settings, "DEFAULT_COVER_IMAGE_FILENAME", "Python编程从入门到实践.jpg")
    return _static_cover_url(filename)


def serialize_customer(customer: Customer, *, include_private: bool = True) -> dict:
    """顾客信息 JSON；对应 Web account 页展示字段。"""
    level = customer.levelid
    discount_percent = (Decimal("1") - level.discountrate) * 100
    available_credit = customer.creditlimit - customer.usedcredit

    data = {
        "customerid": customer.customerid,
        "username": customer.username,
        "name": customer.name,
        "email": customer.email,
        "address": customer.address,
        "balance": str(customer.balance),
        "totalspent": str(customer.totalspent),
        "usedcredit": str(customer.usedcredit),
        "creditlimit": str(customer.creditlimit),
        "available_credit": str(available_credit),
        "levelid": level.levelid,
        "discount_rate": str(level.discountrate),
        "discount_percent": str(discount_percent.quantize(Decimal("0.01"))),
        "can_use_credit": bool(level.canusecredit),
        "registerdate": customer.registerdate.isoformat() if customer.registerdate else None,
    }
    if not include_private:
        data.pop("username", None)
    return data


def _next_level_amount(customer: Customer) -> str | None:
    """距离下一信用等级还需消费多少（与 views.account_recharge 一致）。"""
    thresholds = {
        1: Decimal("1000"),
        2: Decimal("2000"),
        3: Decimal("5000"),
        4: Decimal("10000"),
        5: None,
    }
    nxt = thresholds.get(customer.levelid.levelid)
    if nxt is None:
        return None
    remaining = nxt - customer.totalspent
    if remaining < 0:
        remaining = Decimal("0")
    return str(remaining)


def serialize_account_summary(customer: Customer) -> dict:
    """账户页完整摘要（含升级提示）。"""
    data = serialize_customer(customer)
    data["next_level_amount"] = _next_level_amount(customer)
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


def serialize_order(order: Orders, *, customer: Customer | None = None) -> dict:
    """订单 JSON；customer 传入时附带明细与折扣信息。"""
    details = Orderdetail.objects.filter(orderid=order).select_related("isbn")
    original_amount = sum(d.quantity * d.unitprice for d in details)
    total = order.totalamount or Decimal("0")

    data = {
        "orderid": order.orderid,
        "orderno": order.orderno,
        "orderdate": order.orderdate.isoformat() if order.orderdate else None,
        "shipaddress": order.shipaddress,
        "totalamount": str(total),
        "actualpaid": str(order.actualpaid or 0),
        "unpaid_amount": str(max(total - (order.actualpaid or 0), Decimal("0"))),
        "paymentstatus": order.paymentstatus,
        "status": order.status,
        "original_amount": str(original_amount),
        "discount_amount": str(original_amount - total),
    }

    if customer is not None:
        rate = customer.levelid.discountrate
        data["details"] = [serialize_order_detail_line(d, rate) for d in details]
        data["discount_rate"] = str(rate)
        data["discount_percent"] = str(((Decimal("1") - rate) * 100).quantize(Decimal("0.01")))

    return data
