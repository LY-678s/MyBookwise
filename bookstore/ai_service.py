"""
AI 聊天服务：支持 Google Gemini 与 DeepSeek。

settings.py 中通过 AI_PROVIDER 选择：
  - "gemini"   → GEMINI_API_KEY（Google AI Studio）
  - "deepseek" → DEEPSEEK_API_KEY（https://platform.deepseek.com/）
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any

from django.conf import settings
from django.db.models import Q

from .models import Book, Creditlevel

_BOOK_QUERY_HINTS = (
    "书", "图书", "ISBN", "isbn", "推荐", "作者", "阅读", "购买", "库存", "藏书",
)
_AI_QUERY_STOP_WORDS = {
    "什么", "有没有", "哪些", "怎么", "如何", "可以", "想要", "想找", "帮我",
    "推荐", "相关", "关于", "的书", "书籍", "一本", "一些", "请问", "吗", "呢",
    "the", "and", "for", "with", "book", "books",
}


def _is_book_recommendation_query(message: str) -> bool:
    text = (message or "").strip()
    return any(hint in text for hint in _BOOK_QUERY_HINTS)


def _extract_search_tokens(message: str) -> list[str]:
    tokens = re.findall(r"[\u4e00-\u9fff]+|[A-Za-z0-9]+", message or "")
    seen: set[str] = set()
    result: list[str] = []
    for token in tokens:
        key = token.lower()
        if len(token) < 2 or key in _AI_QUERY_STOP_WORDS or key in seen:
            continue
        seen.add(key)
        result.append(token)
    return result


def _search_books_for_ai(message: str, limit: int = 20) -> list[Book]:
    tokens = _extract_search_tokens(message)
    if not tokens:
        return []

    qs = Book.objects.none()
    for token in tokens:
        qs = qs | Book.objects.filter(
            Q(title__icontains=token)
            | Q(keywords__icontains=token)
            | Q(description__icontains=token)
            | Q(isbn__icontains=token)
        )
    return list(
        qs.distinct()
        .only("isbn", "title", "price", "stockqty")
        .order_by("title")[:limit]
    )


def _format_book_lines(books: list[Book]) -> str:
    return "\n".join(
        f"- 《{book.title}》 ISBN:{book.isbn} 价格:¥{book.price} 库存:{book.stockqty}册"
        for book in books
    )


class AIServiceError(Exception):
    """AI 服务调用失败时抛出。"""


def _provider() -> str:
    return getattr(settings, "AI_PROVIDER", "gemini").strip().lower()


def _get_gemini_api_key() -> str:
    key = getattr(settings, "GEMINI_API_KEY", "") or os.environ.get("GEMINI_API_KEY", "")
    key = (key or "").strip()
    if not key:
        raise AIServiceError(
            "尚未配置 GEMINI_API_KEY。申请地址：https://aistudio.google.com/apikey"
        )
    return key


def _get_deepseek_api_key() -> str:
    key = getattr(settings, "DEEPSEEK_API_KEY", "") or os.environ.get("DEEPSEEK_API_KEY", "")
    key = (key or "").strip()
    if not key:
        raise AIServiceError(
            "尚未配置 DEEPSEEK_API_KEY。申请地址：https://platform.deepseek.com/"
        )
    return key


def is_ai_configured() -> bool:
    """检查当前 AI 提供商是否已配置密钥。"""
    try:
        if _provider() == "deepseek":
            _get_deepseek_api_key()
        else:
            _get_gemini_api_key()
        return True
    except AIServiceError:
        return False


def build_bookstore_system_prompt(user_message: str | None = None) -> str:
    """把书店图书信息和真实业务规则注入系统提示，让 AI 能准确回答用户问题。"""
    user_message = (user_message or "").strip()
    if user_message and _is_book_recommendation_query(user_message):
        matched_books = _search_books_for_ai(user_message)
        if matched_books:
            catalog = _format_book_lines(matched_books)
            catalog_section = (
                "【与用户问题匹配的店内图书（只能推荐以下书籍，不得补充清单外书名或 ISBN）】\n"
                f"{catalog}"
            )
        else:
            catalog_section = (
                f"【与用户问题匹配的店内图书】\n"
                f"（未在店内找到与「{user_message}」相关的图书。"
                "请明确告诉用户：店内暂无该类书籍，建议换个关键词在搜索页查找；"
                "不要编造书名、ISBN 或价格。）"
            )
    else:
        books = Book.objects.all().order_by("title")[:30]
        if books:
            catalog_section = (
                "【当前书店部分图书清单（仅作参考，推荐时仍须与用户问题在店内可搜到的书一致）】\n"
                f"{_format_book_lines(books)}"
            )
        else:
            catalog_section = "【当前书店部分图书清单】\n（当前暂无图书数据）"

    # 读取真实的信用等级规则
    levels = Creditlevel.objects.all().order_by("levelid")
    level_rules = "\n".join([
        f"  - {l.levelid}级：折扣率{l.discountrate*100:.0f}%，信用额度¥{l.creditlimit}，{'可使用信用支付' if l.canusecredit else '不可使用信用支付'}"
        for l in levels
    ])

    return (
        "你是 MyBookwise 网上书店的 AI 助手，名字叫「书小智」。"
        "请用简洁、友好的中文回答用户问题。\n\n"

        "【你的职责】\n"
        "1. 根据用户需求推荐图书（参考下方图书清单）\n"
        "2. 解答购物流程（注册、登录、加购物车、下单、支付、信用额度等）\n"
        "3. 介绍书店功能（搜索、订单管理、会员与积分等）\n"
        "4. 回答一般阅读相关问题\n\n"

        "【会员等级规则】\n"
        "免费开通会员后，购物累计积分（与人民币 1:1），积分决定会员等级：\n"
        "  - 积分 < 1000 → 1级\n"
        "  - 积分 ≥ 1000 → 2级\n"
        "  - 积分 ≥ 2000 → 3级\n"
        "  - 积分 ≥ 5000 → 4级\n"
        "  - 积分 ≥ 10000 → 5级（最高档显示 max）\n\n"
        "各等级具体权益（从数据库读取）：\n"
        f"{level_rules}\n\n"
        "【畅读卡】\n"
        "会员可购买 ¥20/月畅读卡，在等级折扣基础上再乘 7.2 折。\n\n"

        "【支付方式】\n"
        "购书使用在线支付（支持银行卡 / 支付宝）。\n"
        "开通会员后，支付金额与积分 1:1 累计。\n\n"

        "【订单状态】\n"
        "  - 待付款（0）→ 已付款/待发货（1）→ 已完成（2）\n"
        "  - 任何状态 → 已取消（4），取消后余额和信用额度会退回\n\n"

        "【缺货与采购】\n"
        "当图书库存低于最低库存限制（MinStockLimit）时，系统会自动生成缺货记录，\n"
        "并自动向供应商生成采购单补货。\n\n"

        "【注意事项】\n"
        "- 推荐图书时，只能引用上方清单里列出的书名与 ISBN；清单为空时必须如实说明店内没有\n"
        "- 严禁使用模型训练数据中的名书来凑答案（例如 Python Crash Course 等若不在清单中则不可推荐）\n"
        "- 若用户想购买，引导其在网站搜索或浏览首页\n"
        "- 回答要基于上述真实业务规则，不要泛泛而谈\n"
        "- 若问题与书店无关，也可简短回答，但优先引导回书店相关话题\n\n"

        f"{catalog_section}"
    )


def _history_to_gemini_contents(history: list[dict[str, str]]) -> list[dict[str, Any]]:
    contents = []
    for item in history:
        role = item.get("role")
        text = (item.get("content") or "").strip()
        if not text:
            continue
        if role == "user":
            contents.append({"role": "user", "parts": [{"text": text}]})
        elif role == "assistant":
            contents.append({"role": "model", "parts": [{"text": text}]})
    return contents


def _history_to_openai_messages(
    history: list[dict[str, str]], user_message: str
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [
        {"role": "system", "content": build_bookstore_system_prompt(user_message)}
    ]
    for item in history:
        role = item.get("role")
        text = (item.get("content") or "").strip()
        if not text:
            continue
        if role == "user":
            messages.append({"role": "user", "content": text})
        elif role == "assistant":
            messages.append({"role": "assistant", "content": text})
    return messages


def _parse_http_error(exc: urllib.error.HTTPError) -> str:
    body = exc.read().decode("utf-8", errors="replace")
    try:
        err_json = json.loads(body)
        return err_json.get("error", {}).get("message", body)
    except json.JSONDecodeError:
        return body or str(exc)


def _gemini_auth_hint(key: str) -> str:
    if key.startswith("AQ."):
        return (
            " 你的密钥是 Google 新版 AQ. 格式，但当前账号/地区可能无法通过 API 调用。"
            "建议：① 打开 https://console.cloud.google.com/apis/credentials 创建 AIza 开头的密钥；"
            "或 ② 在 settings.py 中设置 AI_PROVIDER = \"deepseek\" 改用 DeepSeek。"
        )
    return ""


def _chat_with_gemini_sdk(
    api_key: str, model: str, history: list[dict[str, str]], user_message: str
) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    contents = _history_to_gemini_contents(history)
    contents.append({"role": "user", "parts": [{"text": user_message}]})

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=build_bookstore_system_prompt(user_message),
            temperature=0.3,
            max_output_tokens=1024,
        ),
    )
    reply = (response.text or "").strip()
    if not reply:
        raise AIServiceError("AI 未返回有效内容，请换个问题试试。")
    return reply


def _chat_with_gemini_rest(
    api_key: str, model: str, history: list[dict[str, str]], user_message: str, timeout: int
) -> str:
    contents = _history_to_gemini_contents(history)
    contents.append({"role": "user", "parts": [{"text": user_message}]})
    payload = {
        "systemInstruction": {"parts": [{"text": build_bookstore_system_prompt(user_message)}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1024},
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    candidates = data["candidates"]
    parts = candidates[0]["content"]["parts"]
    reply = "".join(part.get("text", "") for part in parts).strip()
    if not reply:
        raise AIServiceError("AI 未返回有效内容，请换个问题试试。")
    return reply


def _chat_with_gemini(history: list[dict[str, str]], user_message: str) -> str:
    api_key = _get_gemini_api_key()
    model = getattr(settings, "GEMINI_MODEL", "gemini-2.0-flash")
    timeout = getattr(settings, "AI_REQUEST_TIMEOUT", 30)

    try:
        return _chat_with_gemini_sdk(api_key, model, history, user_message)
    except ImportError:
        pass
    except Exception as exc:
        err = str(exc)
        if "401" in err or "UNAUTHENTICATED" in err:
            raise AIServiceError(
                f"Gemini 认证失败（401）。{_gemini_auth_hint(api_key)}"
            ) from exc
        if "429" in err or "RESOURCE_EXHAUSTED" in err or "quota" in err.lower():
            raise AIServiceError(
                "Gemini 免费额度已用完或被限流（429）。"
                "请稍后再试，或在 settings.py 中改用 AI_PROVIDER = \"deepseek\"。"
            ) from exc
        raise AIServiceError(f"Gemini 调用失败：{err}") from exc

    try:
        return _chat_with_gemini_rest(api_key, model, history, user_message, timeout)
    except urllib.error.HTTPError as exc:
        message = _parse_http_error(exc)
        if exc.code == 401:
            raise AIServiceError(
                f"Gemini 认证失败（401）：{message}{_gemini_auth_hint(api_key)}"
            ) from exc
        if exc.code == 429:
            raise AIServiceError(
                "Gemini 免费额度已用完或被限流（429）。"
                "请在 settings.py 中改用 AI_PROVIDER = \"deepseek\"。"
            ) from exc
        raise AIServiceError(f"Gemini 服务返回错误（{exc.code}）：{message}") from exc
    except urllib.error.URLError as exc:
        raise AIServiceError(f"无法连接 Gemini，请检查网络或 VPN：{exc.reason}") from exc
    except TimeoutError as exc:
        raise AIServiceError("Gemini 响应超时，请稍后再试。") from exc


def _chat_with_deepseek(history: list[dict[str, str]], user_message: str) -> str:
    api_key = _get_deepseek_api_key()
    model = getattr(settings, "DEEPSEEK_MODEL", "deepseek-chat")
    api_base = getattr(settings, "DEEPSEEK_API_BASE", "https://api.deepseek.com").rstrip("/")
    timeout = getattr(settings, "AI_REQUEST_TIMEOUT", 60)

    messages = _history_to_openai_messages(history, user_message)
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 1024,
        "stream": False,
    }
    url = f"{api_base}/chat/completions"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        message = _parse_http_error(exc)
        raise AIServiceError(f"DeepSeek 服务返回错误（{exc.code}）：{message}") from exc
    except urllib.error.URLError as exc:
        raise AIServiceError(f"无法连接 DeepSeek：{exc.reason}") from exc
    except TimeoutError as exc:
        raise AIServiceError("DeepSeek 响应超时，请稍后再试。") from exc

    reply = data["choices"][0]["message"]["content"].strip()
    if not reply:
        raise AIServiceError("AI 未返回有效内容，请换个问题试试。")
    return reply


def chat_with_ai(history: list[dict[str, str]], user_message: str) -> str:
    user_message = (user_message or "").strip()
    if not user_message:
        raise AIServiceError("消息不能为空。")
    if len(user_message) > 2000:
        raise AIServiceError("消息过长，请控制在 2000 字以内。")

    if _provider() == "deepseek":
        return _chat_with_deepseek(history, user_message)
    return _chat_with_gemini(history, user_message)
