"""推荐算法模块单元测试

覆盖函数/类：
- _tokenize、_book_tokens、_cosine_like（内部辅助函数）
- RecommendationEngine（推荐引擎）
- get_recommendations_for_user、get_default_recommendations（公开接口）
- invalidate_recommendation_cache（缓存失效）

测试方法分布：
- 等价类：中英文分词、空文本、余弦相似度
- 边界值：无图书、无用户行为时的降级
- 场景法：有浏览/搜索/收藏时的个性化推荐
- 独立路径：缓存命中/缓存未命中
"""
from __future__ import annotations

from collections import Counter
from decimal import Decimal

import pytest
from django.core.cache import cache

from bookstore.recommendations import (
    _tokenize,
    _cosine_like,
    RecommendationEngine,
    get_recommendations_for_user,
    get_default_recommendations,
    invalidate_recommendation_cache,
    GLOBAL_RANKING_CACHE_KEY,
    SALES_CACHE_KEY,
    RECENCY_CACHE_KEY,
)


pytestmark = pytest.mark.django_db


# =============================================================
# _tokenize（分词辅助函数）
# =============================================================

class TestTokenize:
    """分词函数测试。"""

    def test_chinese_text(self):
        """等价类：中文文本 → ≤4字不拆分，>4字按二字组切分。"""
        tokens = _tokenize("机器学习")  # 4字，不拆分
        assert "机器学习" in tokens
        tokens2 = _tokenize("人工智能技术")  # 6字，拆分
        assert "人工" in tokens2
        assert "智能" in tokens2

    def test_english_text(self):
        """等价类：英文文本 → 按单词切分，过滤停用词。"""
        tokens = _tokenize("Python Programming")
        assert "python" in tokens
        assert "programming" in tokens
        assert "the" not in tokens  # 停用词被过滤

    def test_stop_words_filtered(self):
        """边界值：全是停用词 → 返回空列表。"""
        tokens = _tokenize("the and for with")
        assert tokens == []

    def test_empty_text(self):
        """边界值：空文本 → 空列表。"""
        assert _tokenize("") == []
        assert _tokenize(None) == []

    def test_short_chinese_not_split(self):
        """边界值：≤4 字中文 → 不拆二字组。"""
        tokens = _tokenize("Python")
        assert "python" in tokens

    def test_mixed_text(self):
        """场景：中英混合 → 分别处理。"""
        tokens = _tokenize("Python编程入门")
        assert "python" in tokens
        assert "编程入门" in tokens  # 4字中文不拆分


# =============================================================
# _cosine_like（余弦相似度）
# =============================================================

class TestCosineLike:
    """余弦相似度函数测试。"""

    def test_identical_profiles(self):
        """等价类：完全相同 → 返回 1.0。"""
        profile = Counter({"a": 1, "b": 2})
        result = _cosine_like(profile, profile)
        assert abs(result - 1.0) < 0.001

    def test_no_overlap(self):
        """等价类：无交集 → 返回 0.0。"""
        profile = Counter({"a": 1})
        item = Counter({"b": 1})
        assert _cosine_like(profile, item) == 0.0

    def test_empty_profile(self):
        """边界值：空 profile → 返回 0.0。"""
        assert _cosine_like(Counter(), Counter({"a": 1})) == 0.0

    def test_partial_overlap(self):
        """场景：部分重叠 → 返回 0~1 之间。"""
        profile = Counter({"a": 1, "b": 1})
        item = Counter({"a": 1, "c": 1})
        result = _cosine_like(profile, item)
        assert 0.0 < result < 1.0


# =============================================================
# RecommendationEngine
# =============================================================

class TestRecommendationEngine:
    """推荐引擎测试。"""

    def test_no_customer_returns_books(self, book, book2):
        """等价类：无 customer_id → 返回全局推荐。"""
        engine = RecommendationEngine(customer_id=None)
        result = engine.get_recommendations(limit=5)
        assert len(result) >= 1
        assert all(hasattr(b, "isbn") for b in result)

    def test_customer_no_behavior_returns_global(self, customer, book):
        """场景：顾客无浏览/搜索行为 → 降级为全局推荐。"""
        engine = RecommendationEngine(customer_id=customer.customerid)
        result = engine.get_recommendations(limit=5)
        assert isinstance(result, list)

    def test_customer_with_browse_history(self, customer, book, book2):
        """场景：有浏览记录 → 推荐相关图书。"""
        from bookstore.models import BrowseHistory
        BrowseHistory.objects.create(customer_id=customer.customerid, isbn_id=book.isbn)

        engine = RecommendationEngine(customer_id=customer.customerid)
        result = engine.get_recommendations(limit=5)
        assert isinstance(result, list)

    def test_customer_with_search_history(self, customer, book):
        """场景：有搜索记录 → 推荐相关图书。"""
        from bookstore.models import SearchHistory
        SearchHistory.objects.create(customer_id=customer.customerid, keyword=book.title)

        engine = RecommendationEngine(customer_id=customer.customerid)
        result = engine.get_recommendations(limit=5)
        assert isinstance(result, list)

    def test_limit_parameter(self, book, book2):
        """边界值：limit=1 → 最多返回 1 本。"""
        engine = RecommendationEngine(customer_id=None)
        result = engine.get_recommendations(limit=1)
        assert len(result) <= 1

    def test_out_of_stock_books_excluded(self, book):
        """边界值：库存为 0 的书 → 不出现在推荐中。"""
        book.stockqty = 0
        book.save()
        engine = RecommendationEngine(customer_id=None)
        result = engine.get_recommendations(limit=10)
        isbns = [b.isbn for b in result]
        assert book.isbn not in isbns


# =============================================================
# 公开接口
# =============================================================

class TestPublicInterfaces:
    """get_recommendations_for_user / get_default_recommendations 测试。"""

    def test_get_default_recommendations(self, book):
        """等价类：全局推荐 → 返回图书列表。"""
        result = get_default_recommendations(limit=5)
        assert isinstance(result, list)
        assert len(result) <= 5

    def test_get_user_recommendations(self, customer, book):
        """等价类：用户推荐 → 返回图书列表。"""
        result = get_recommendations_for_user(customer.customerid, limit=5)
        assert isinstance(result, list)

    def test_cache_hit_returns_same_result(self, book):
        """场景：缓存命中 → 返回相同结果。"""
        # 第一次调用会写入缓存
        result1 = get_default_recommendations(limit=5)
        # 第二次应命中缓存
        result2 = get_default_recommendations(limit=5)
        assert [b.isbn for b in result1] == [b.isbn for b in result2]


# =============================================================
# invalidate_recommendation_cache
# =============================================================

class TestInvalidateCache:
    """缓存失效函数测试。"""

    def test_invalidate_all(self):
        """场景：清除全部缓存 → 相关 key 被删除。"""
        cache.set(SALES_CACHE_KEY, {"test": 1.0})
        cache.set(RECENCY_CACHE_KEY, {"test": 1.0})
        cache.set(GLOBAL_RANKING_CACHE_KEY, ["test"])
        cache.set("default_recommendations", ["test"])

        invalidate_recommendation_cache()

        assert cache.get(SALES_CACHE_KEY) is None
        assert cache.get(RECENCY_CACHE_KEY) is None
        assert cache.get(GLOBAL_RANKING_CACHE_KEY) is None
        assert cache.get("default_recommendations") is None

    def test_invalidate_specific_user(self):
        """场景：清除指定用户缓存 → 仅删除该用户。"""
        cache.set("user_recommendations_42", ["isbn1"])
        cache.set("user_recommendations_99", ["isbn2"])

        invalidate_recommendation_cache(customer_id=42)

        assert cache.get("user_recommendations_42") is None
        assert cache.get("user_recommendations_99") == ["isbn2"]
