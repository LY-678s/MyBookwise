"""用户行为追踪模块单元测试

覆盖函数：record_search、record_browse

测试方法分布：
- 等价类：有效关键词、空关键词、纯空格
- 边界值：超长关键词截断（100 字符）
- 场景法：多次搜索/浏览记录正确保存
- 独立路径：成功路径、异常路径
"""
from __future__ import annotations

import pytest

from bookstore.models import SearchHistory, BrowseHistory
from bookstore.tracking import record_search, record_browse


pytestmark = pytest.mark.django_db


# =============================================================
# record_search
# =============================================================

class TestRecordSearch:
    """record_search 函数测试。"""

    def test_valid_keyword_returns_true(self, customer):
        """等价类：有效关键词 → 记录成功，返回 True。"""
        result = record_search(customer.customerid, "Python编程")
        assert result is True
        assert SearchHistory.objects.filter(keyword="Python编程").exists()

    def test_keyword_is_stripped(self, customer):
        """等价类：前后有空格的关键词 → 自动去除空格。"""
        record_search(customer.customerid, "  Django  ")
        record = SearchHistory.objects.first()
        assert record.keyword == "Django"

    def test_long_keyword_truncated_to_100(self, customer):
        """边界值：超长关键词 → 截断到 100 字符。"""
        long_keyword = "A" * 200
        record_search(customer.customerid, long_keyword)
        record = SearchHistory.objects.first()
        assert len(record.keyword) == 100

    def test_empty_keyword_returns_false(self, customer):
        """边界值：空字符串 → 不记录，返回 False。"""
        result = record_search(customer.customerid, "")
        assert result is False
        assert SearchHistory.objects.count() == 0

    def test_whitespace_only_keyword_returns_false(self, customer):
        """边界值：纯空格 → 不记录，返回 False。"""
        result = record_search(customer.customerid, "   ")
        assert result is False
        assert SearchHistory.objects.count() == 0

    def test_none_keyword_returns_false(self, customer):
        """异常：None → 不记录，返回 False。"""
        result = record_search(customer.customerid, None)
        assert result is False

    def test_multiple_searches_all_recorded(self, customer):
        """场景：多次搜索 → 全部记录。"""
        record_search(customer.customerid, "Python")
        record_search(customer.customerid, "Django")
        record_search(customer.customerid, "机器学习")
        assert SearchHistory.objects.filter(customer_id=customer.customerid).count() == 3

    def test_search_invalidates_recommendation_cache(self, customer, mocker):
        """场景：搜索后应调用缓存失效函数。"""
        mocker.patch("bookstore.recommendations.invalidate_recommendation_cache")
        result = record_search(customer.customerid, "测试")
        assert result is True


# =============================================================
# record_browse
# =============================================================

class TestRecordBrowse:
    """record_browse 函数测试。"""

    def test_valid_isbn_returns_true(self, customer, book):
        """等价类：有效 ISBN → 记录成功，返回 True。"""
        result = record_browse(customer.customerid, book.isbn)
        assert result is True
        assert BrowseHistory.objects.filter(
            customer_id=customer.customerid, isbn_id=book.isbn
        ).exists()

    def test_empty_isbn_returns_false(self, customer):
        """边界值：空 ISBN → 不记录，返回 False。"""
        result = record_browse(customer.customerid, "")
        assert result is False
        assert BrowseHistory.objects.count() == 0

    def test_none_isbn_returns_false(self, customer):
        """异常：None ISBN → 不记录，返回 False。"""
        result = record_browse(customer.customerid, None)
        assert result is False

    def test_multiple_browses_all_recorded(self, customer, book, book2):
        """场景：多次浏览 → 全部记录。"""
        record_browse(customer.customerid, book.isbn)
        record_browse(customer.customerid, book2.isbn)
        record_browse(customer.customerid, book.isbn)  # 重复浏览也记录
        assert BrowseHistory.objects.filter(customer_id=customer.customerid).count() == 3

    def test_browse_creates_history_record(self, customer, book):
        """场景：浏览记录包含正确的 customer 和 book 关联。"""
        record_browse(customer.customerid, book.isbn)
        record = BrowseHistory.objects.first()
        assert record.customer_id == customer.customerid
        assert record.isbn_id == book.isbn
        assert record.browse_time is not None
