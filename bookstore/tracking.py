"""
用户行为追踪模块

提供搜索记录和浏览记录的保存功能，供视图层调用。
"""

from django.db import IntegrityError
import logging

from .models import SearchHistory, BrowseHistory

logger = logging.getLogger(__name__)


def record_search(customer_id: int, keyword: str) -> bool:
    """
    记录用户搜索行为

    Args:
        customer_id: 用户ID
        keyword: 搜索关键词

    Returns:
        bool: 是否记录成功
    """
    if not keyword or not keyword.strip():
        return False

    try:
        SearchHistory.objects.create(
            customer_id=customer_id,
            keyword=keyword.strip()[:100]  # 限制关键词长度
        )
        from .recommendations import invalidate_recommendation_cache
        invalidate_recommendation_cache(customer_id=customer_id)
        return True
    except IntegrityError:
        logger.warning(f"Failed to record search for customer {customer_id}")
        return False
    except Exception:  # pylint: disable=broad-exception-caught
        logger.exception(f"Error recording search for customer {customer_id}")
        return False


def get_recent_search_keywords(customer_id: int, limit: int = 10) -> list[str]:
    """最近搜索词（去重，保留时间顺序）。"""
    seen: set[str] = set()
    keywords: list[str] = []
    rows = (
        SearchHistory.objects.filter(customer_id=customer_id)
        .order_by("-search_time")
        .values_list("keyword", flat=True)[:50]
    )
    for raw in rows:
        kw = (raw or "").strip()
        if not kw:
            continue
        key = kw.casefold()
        if key in seen:
            continue
        seen.add(key)
        keywords.append(kw)
        if len(keywords) >= limit:
            break
    return keywords


def record_browse(customer_id: int, isbn: str) -> bool:
    """
    记录用户浏览图书行为

    Args:
        customer_id: 用户ID
        isbn: 图书ISBN

    Returns:
        bool: 是否记录成功
    """
    if not isbn:
        return False

    try:
        BrowseHistory.objects.create(
            customer_id=customer_id,
            isbn_id=isbn
        )
        from .recommendations import invalidate_recommendation_cache
        invalidate_recommendation_cache(customer_id=customer_id)
        return True
    except IntegrityError:
        logger.warning(f"Failed to record browse for customer {customer_id}, ISBN {isbn}")
        return False
    except Exception:  # pylint: disable=broad-exception-caught
        logger.exception(f"Error recording browse for customer {customer_id}")
        return False
