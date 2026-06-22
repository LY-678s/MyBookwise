"""
个性化推荐算法模块 - 优化版

优化点：
1. 销量分数和时间衰减分数预计算并缓存
2. 用户推荐使用 SQL 查询替代遍历
3. 添加多层缓存机制

推荐分数计算公式：
    最终分数 = 销量分数 × 0.4 + 时间衰减分数 × 0.2 + 用户倾向度 × 0.4
"""

from django.db.models import Sum, Max, Q
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from typing import List, Set, Optional
import logging

from .models import Book, Orderdetail, SearchHistory, BrowseHistory

logger = logging.getLogger(__name__)

# 缓存配置
SALES_CACHE_KEY = 'recommendation_sales_scores'
RECENCY_CACHE_KEY = 'recommendation_recency_scores'
SALES_CACHE_TIMEOUT = 3600 * 6  # 6小时
RECENCY_CACHE_TIMEOUT = 3600  # 1小时


class RecommendationEngine:
    """推荐引擎 - 优化版"""

    # 权重配置
    SALES_WEIGHT = 0.4
    RECENCY_WEIGHT = 0.2
    USER_PREFERENCE_WEIGHT = 0.4

    # 时间衰减配置
    RECENCY_DAYS = 30
    RECENCY_DECAY_RATE = 0.1

    # 用户偏好配置
    PREFERENCE_KEYWORD_LIMIT = 50  # 关键词数量限制
    PREFERENCE_BOOK_LIMIT = 500  # 候选书籍数量

    def __init__(self, customer_id: Optional[int] = None):
        self.customer_id = customer_id

    def get_recommendations(self, limit: int = 20) -> List[Book]:
        """
        获取推荐书籍列表 - 优化版
        """
        # 获取用户偏好书籍集合
        preference_isbns = self._get_preference_isbns()
        
        # 获取全局排名（销量+时间衰减）
        global_scores = self._get_global_scores()
        
        # 如果有用户偏好，混合排序
        if preference_isbns:
            scored_books = []
            for isbn, score_data in global_scores.items():
                # 用户偏好书籍获得额外加分
                pref_boost = 0.5 if isbn in preference_isbns else 0
                total = score_data['total_score'] + pref_boost * self.USER_PREFERENCE_WEIGHT
                scored_books.append((isbn, total, score_data['book']))
            
            # 混合排序
            scored_books.sort(key=lambda x: x[1], reverse=True)
            result = [book for _, _, book in scored_books[:limit]]
        else:
            # 无偏好，按全局排名
            result = [score_data['book'] for _, score_data in list(global_scores.items())[:limit]]
        
        return result

    def _get_preference_isbns(self) -> Set[str]:
        """获取用户偏好书籍的ISBN集合 - 使用SQL优化"""
        if not self.customer_id:
            return set()
        
        # 获取用户搜索和浏览记录中的关键词
        keywords = self._get_user_keywords()
        if not keywords:
            return set()
        
        # 用SQL直接查询匹配的书籍
        query = Q()
        for kw in keywords:
            query |= Q(title__icontains=kw) | Q(keywords__icontains=kw)
        
        if not query:
            return set()
        
        # 只返回有库存的书籍
        matching_books = Book.objects.filter(query, stockqty__gt=0).values_list('isbn', flat=True)[:self.PREFERENCE_BOOK_LIMIT]
        return set(matching_books)

    def _get_user_keywords(self) -> List[str]:
        """获取用户偏好关键词"""
        keywords = set()
        
        # 获取搜索关键词
        search_records = SearchHistory.objects.filter(
            customer_id=self.customer_id
        ).values_list('keyword', flat=True)[:self.PREFERENCE_KEYWORD_LIMIT]
        
        for kw in search_records:
            if kw:
                keywords.update([w.strip().lower() for w in kw.split() if len(w) > 1])
        
        # 获取浏览书籍的关键词
        browse_records = BrowseHistory.objects.filter(
            customer_id=self.customer_id
        ).select_related('isbn')[:self.PREFERENCE_KEYWORD_LIMIT]
        
        for record in browse_records:
            book = record.isbn
            if book.keywords:
                keywords.update([w.strip().lower() for w in book.keywords.split(',') if len(w) > 1])
            # 从书名提取关键词
            title_words = book.title.replace('(', ' ').replace(')', ' ').replace('-', ' ')
            keywords.update([w.lower() for w in title_words.split() if len(w) > 1])
        
        return list(keywords)[:self.PREFERENCE_KEYWORD_LIMIT]

    def _get_global_scores(self) -> dict:
        """
        获取全局分数（销量+时间衰减）- 带缓存
        """
        # 尝试从缓存获取
        sales_scores = cache.get(SALES_CACHE_KEY)
        recency_scores = cache.get(RECENCY_CACHE_KEY)
        
        # 计算缺少的分数
        if sales_scores is None:
            sales_scores = self._calculate_sales_scores()
            cache.set(SALES_CACHE_KEY, sales_scores, SALES_CACHE_TIMEOUT)
        
        if recency_scores is None:
            recency_scores = self._calculate_recency_scores()
            cache.set(RECENCY_CACHE_KEY, recency_scores, RECENCY_CACHE_TIMEOUT)
        
        # 获取有库存的书籍
        books = Book.objects.filter(stockqty__gt=0).only('isbn', 'title', 'publisher', 'price', 'keywords', 'stockqty', 'location', 'minstocklimit', 'coverimage')
        
        scores = {}
        for book in books:
            isbn = book.isbn
            sales = sales_scores.get(isbn, 0)
            recency = recency_scores.get(isbn, 0)
            
            total_score = sales * self.SALES_WEIGHT + recency * self.RECENCY_WEIGHT
            
            scores[isbn] = {
                'total_score': total_score,
                'sales_score': sales,
                'recency_score': recency,
                'book': book
            }
        
        # 按分数排序
        sorted_scores = sorted(scores.items(), key=lambda x: x[1]['total_score'], reverse=True)
        
        return dict(sorted_scores[:1000])  # 只保留前1000本

    def _calculate_sales_scores(self) -> dict:
        """计算销量分数 - 归一化到 0-1"""
        sales_data = Orderdetail.objects.values('isbn').annotate(
            total_qty=Sum('quantity')
        ).order_by('-total_qty')
        
        if not sales_data:
            return {}
        
        max_sales = sales_data[0]['total_qty'] or 1
        min_sales = sales_data.last()['total_qty'] or 0
        sales_range = max(max_sales - min_sales, 1)
        
        return {
            item['isbn']: (item['total_qty'] or 0 - min_sales) / sales_range
            for item in sales_data
        }

    def _calculate_recency_scores(self) -> dict:
        """计算时间衰减分数"""
        cutoff_date = timezone.now() - timedelta(days=self.RECENCY_DAYS)
        
        recent_orders = Orderdetail.objects.filter(
            orderid__orderdate__gte=cutoff_date
        ).values('isbn').annotate(
            recent_qty=Sum('quantity'),
            latest_date=Max('orderid__orderdate')
        )
        
        if not recent_orders:
            return {}
        
        max_recency = recent_orders[0]['recent_qty'] or 1
        
        scores = {}
        now = timezone.now()
        for item in recent_orders:
            isbn = item['isbn']
            recent_qty = item['recent_qty'] or 0
            days_ago = (now - item['latest_date']).days
            
            base_score = recent_qty / max_recency
            decay = (1 - self.RECENCY_DECAY_RATE) ** days_ago
            scores[isbn] = base_score * decay
        
        return scores


def get_recommendations_for_user(customer_id: int, limit: int = 20) -> List[Book]:
    """为指定用户获取推荐 - 带缓存"""
    # 短期缓存用户推荐结果（5分钟）
    cache_key = f'user_recommendations_{customer_id}'
    cached = cache.get(cache_key)
    
    if cached is not None:
        # 从缓存获取，只需要取前limit个
        isbns = cached[:limit]
        if isbns:
            books = Book.objects.filter(isbn__in=isbns, stockqty__gt=0)
            # 保持顺序
            book_dict = {b.isbn: b for b in books}
            return [book_dict[isbn] for isbn in isbns if isbn in book_dict]
    
    # 计算推荐
    engine = RecommendationEngine(customer_id=customer_id)
    books = engine.get_recommendations(limit=1000)  # 计算更多用于缓存
    
    # 缓存ISBN列表
    isbn_list = [b.isbn for b in books]
    cache.set(cache_key, isbn_list, 300)  # 5分钟
    
    return books[:limit]


def get_default_recommendations(limit: int = 20) -> List[Book]:
    """为未登录用户获取推荐 - 使用全局排名"""
    # 尝试从缓存获取
    cache_key = 'default_recommendations'
    cached = cache.get(cache_key)
    
    if cached is not None:
        isbns = cached[:limit]
        if isbns:
            books = Book.objects.filter(isbn__in=isbns, stockqty__gt=0)
            book_dict = {b.isbn: b for b in books}
            return [book_dict[isbn] for isbn in isbns if isbn in book_dict]
    
    # 计算全局排名
    engine = RecommendationEngine(customer_id=None)
    books = engine.get_recommendations(limit=1000)
    
    # 缓存
    isbn_list = [b.isbn for b in books]
    cache.set(cache_key, isbn_list, 300)  # 5分钟
    
    return books[:limit]


def invalidate_recommendation_cache():
    """清除推荐缓存"""
    cache.delete(SALES_CACHE_KEY)
    cache.delete(RECENCY_CACHE_KEY)
    cache.delete('default_recommendations')
