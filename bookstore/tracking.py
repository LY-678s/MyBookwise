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
