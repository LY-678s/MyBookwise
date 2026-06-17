"""
顾客 Token 管理（基于 Django Cache，无需新增数据库表）

Web 端用 Session 存 customer_id；APP 端用 Token，映射关系缓存在内存/Redis 中。
"""
from __future__ import annotations

import secrets

from django.core.cache import cache

# Token 有效期：7 天（秒）
TOKEN_TTL = 60 * 60 * 24 * 7

_TOKEN_PREFIX = "customer_token:"
_CUSTOMER_TOKENS_PREFIX = "customer_tokens:"  # 同一顾客仅保留最新 Token（单设备登录）


def create_token(customer_id: int) -> str:
    """登录/注册成功后签发 Token，并作废该顾客旧 Token。"""
    revoke_tokens_for_customer(customer_id)
    token = secrets.token_hex(20)
    cache.set(f"{_TOKEN_PREFIX}{token}", customer_id, timeout=TOKEN_TTL)
    cache.set(f"{_CUSTOMER_TOKENS_PREFIX}{customer_id}", token, timeout=TOKEN_TTL)
    return token


def get_customer_id(token: str) -> int | None:
    """根据 Token 解析 customer_id；无效或过期返回 None。"""
    if not token:
        return None
    return cache.get(f"{_TOKEN_PREFIX}{token}")


def revoke_token(token: str) -> None:
    """注销：删除 Token 映射。"""
    customer_id = cache.get(f"{_TOKEN_PREFIX}{token}")
    cache.delete(f"{_TOKEN_PREFIX}{token}")
    if customer_id is not None:
        cached = cache.get(f"{_CUSTOMER_TOKENS_PREFIX}{customer_id}")
        if cached == token:
            cache.delete(f"{_CUSTOMER_TOKENS_PREFIX}{customer_id}")


def revoke_tokens_for_customer(customer_id: int) -> None:
    """使某顾客全部 Token 失效（重新登录时调用）。"""
    old = cache.get(f"{_CUSTOMER_TOKENS_PREFIX}{customer_id}")
    if old:
        cache.delete(f"{_TOKEN_PREFIX}{old}")
    cache.delete(f"{_CUSTOMER_TOKENS_PREFIX}{customer_id}")
