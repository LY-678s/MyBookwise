"""
统一购物车存储 — Web 与 APP 共用同一份数据。

按 customer_id 存入 Django Cache（key: cart:{customer_id}），
Web 端不再使用 request.session['cart']，APP 与网页登录同一账号后购物车一致。

数据结构：{ "isbn": {"quantity": n}, ... }
"""
from django.core.cache import cache

_CART_PREFIX = "cart:"
_CART_TTL = 60 * 60 * 24 * 7  # 7 天


def get_cart(customer_id: int) -> dict:
    """读取某顾客的购物车。"""
    return cache.get(f"{_CART_PREFIX}{customer_id}", {})


def save_cart(customer_id: int, cart: dict) -> None:
    """保存购物车。"""
    cache.set(f"{_CART_PREFIX}{customer_id}", cart, timeout=_CART_TTL)


def clear_cart(customer_id: int) -> None:
    """清空购物车（下单成功后调用）。"""
    cache.delete(f"{_CART_PREFIX}{customer_id}")
