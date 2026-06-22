"""
AI 聊天历史 — Web 与 APP 共用（按 customer_id 存入 Django Cache）。

- 已登录：读写 cache（key: ai_chat:{customer_id}），Web 与 APP 同步
- 未登录：Web 临时使用 session，登录/注册时合并进 cache
"""
from django.core.cache import cache
from django.http import HttpRequest

_AI_PREFIX = "ai_chat:"
_AI_TTL = 60 * 60 * 24 * 7  # 7 天
_MAX_MESSAGES = 20
_SESSION_KEY = "ai_chat_history"


def get_ai_history(customer_id: int) -> list:
    history = cache.get(f"{_AI_PREFIX}{customer_id}", [])
    if not isinstance(history, list):
        history = []
    return history[-_MAX_MESSAGES:]


def save_ai_history(customer_id: int, history: list) -> None:
    cache.set(f"{_AI_PREFIX}{customer_id}", history[-_MAX_MESSAGES:], timeout=_AI_TTL)


def clear_ai_history(customer_id: int) -> None:
    cache.delete(f"{_AI_PREFIX}{customer_id}")


def _session_history(request: HttpRequest) -> list:
    history = request.session.get(_SESSION_KEY, [])
    if not isinstance(history, list):
        history = []
    return history[-_MAX_MESSAGES:]


def get_ai_history_for_request(request: HttpRequest) -> list:
    customer_id = request.session.get("customer_id")
    if customer_id:
        return get_ai_history(customer_id)
    return _session_history(request)


def save_ai_history_for_request(request: HttpRequest, history: list) -> None:
    trimmed = history[-_MAX_MESSAGES:]
    customer_id = request.session.get("customer_id")
    if customer_id:
        save_ai_history(customer_id, trimmed)
        request.session.pop(_SESSION_KEY, None)
    else:
        request.session[_SESSION_KEY] = trimmed
    request.session.modified = True


def clear_ai_history_for_request(request: HttpRequest) -> None:
    customer_id = request.session.get("customer_id")
    if customer_id:
        clear_ai_history(customer_id)
    request.session.pop(_SESSION_KEY, None)
    request.session.modified = True


def attach_customer_ai_history(request: HttpRequest, customer_id: int) -> None:
    """登录/注册后，将未登录时的 session 历史合并进该顾客的 cache。"""
    session_hist = _session_history(request)
    request.session.pop(_SESSION_KEY, None)
    if session_hist:
        combined = get_ai_history(customer_id) + session_hist
        save_ai_history(customer_id, combined)
    request.session.modified = True
