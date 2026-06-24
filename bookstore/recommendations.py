"""
Book recommendation engine.

The homepage expects a ranked list of Book objects.  This module keeps that
contract, but builds the ranking from common bookstore signals:

1. global popularity: total sales and recent sales
2. user behavior: recent browse history and search history
3. content similarity: title, keywords and description overlap

Performance notes:
- expensive global scores are cached for hours
- per-user recommendation ISBN lists are cached briefly
- personalized scoring only evaluates a bounded candidate set instead of the
  whole book table
"""

from collections import Counter
from datetime import timedelta
import math
import random
import re
import time
from typing import Dict, List, Optional, Sequence, Set, Tuple

from django.core.cache import cache
from django.db.models import Max, Q, Sum
from django.utils import timezone

from .models import Book, BookFavorite, BrowseHistory, Orderdetail, SearchHistory


SALES_CACHE_KEY = "recommendation_sales_scores"
RECENCY_CACHE_KEY = "recommendation_recency_scores"
GLOBAL_RANKING_CACHE_KEY = "recommendation_global_ranking"
SALES_CACHE_TIMEOUT = 3600 * 6
RECENCY_CACHE_TIMEOUT = 3600
GLOBAL_RANKING_CACHE_TIMEOUT = 1800

FEED_CACHE_TIMEOUT = 300
FEED_RANKED_SIZE = 800
FEED_EXPLORE_SIZE = 600
FEED_SHUFFLE_HEAD = 36


TOKEN_RE = re.compile(r"[\u4e00-\u9fff]+|[A-Za-z0-9]+")
STOP_WORDS = {
    "the", "and", "for", "with", "from", "into", "this", "that", "book",
    "edition", "introduction", "a", "an", "of", "to", "in", "on", "by",
}


def _tokenize(text: Optional[str]) -> List[str]:
    """Split mixed Chinese/English book text into compact matching tokens."""
    if not text:
        return []

    tokens: List[str] = []
    for raw in TOKEN_RE.findall(text.lower()):
        if raw in STOP_WORDS:
            continue
        if re.fullmatch(r"[\u4e00-\u9fff]+", raw):
            if len(raw) <= 4:
                tokens.append(raw)
            else:
                tokens.extend(raw[i:i + 2] for i in range(len(raw) - 1))
        elif len(raw) > 1:
            tokens.append(raw)
    return tokens


def _book_tokens(book: Book) -> Counter:
    tokens = Counter()
    tokens.update({token: 3.0 for token in _tokenize(book.keywords)})
    tokens.update({token: 2.0 for token in _tokenize(book.title)})
    tokens.update({token: 1.0 for token in _tokenize(getattr(book, "description", None))})
    return tokens


def _cosine_like(profile: Counter, item: Counter) -> float:
    if not profile or not item:
        return 0.0

    dot = sum(profile[token] * item[token] for token in item.keys() & profile.keys())
    if dot <= 0:
        return 0.0

    profile_norm = math.sqrt(sum(weight * weight for weight in profile.values()))
    item_norm = math.sqrt(sum(weight * weight for weight in item.values()))
    return dot / max(profile_norm * item_norm, 1.0)


class RecommendationEngine:
    """Rank books for anonymous users or a specific customer."""

    SALES_WEIGHT = 0.35
    RECENCY_WEIGHT = 0.20
    CONTENT_WEIGHT = 0.40
    SEED_BOOK_WEIGHT = 0.05

    RECENCY_DAYS = 30
    RECENCY_DECAY_RATE = 0.08

    RECENT_BROWSE_LIMIT = 30
    RECENT_FAVORITE_LIMIT = 50
    RECENT_SEARCH_LIMIT = 20
    PROFILE_TOKEN_LIMIT = 40
    CANDIDATE_TOKEN_LIMIT = 12
    CANDIDATE_BOOK_LIMIT = 700
    GLOBAL_POOL_LIMIT = 1000

    def __init__(self, customer_id: Optional[int] = None):
        self.customer_id = customer_id

    def get_recommendations(self, limit: int = 20) -> List[Book]:
        if not self.customer_id:
            return self._books_from_ranked_isbns(self._get_global_ranking()[:limit])

        profile, interacted_isbns, favorite_isbns = self._build_user_profile()
        if not profile:
            return self._books_from_ranked_isbns(self._get_global_ranking()[:limit])

        global_scores = self._get_global_score_map()
        candidate_isbns = self._get_candidate_isbns(profile, interacted_isbns)
        ranked: List[Tuple[str, float]] = []

        books = Book.objects.filter(
            isbn__in=candidate_isbns,
            stockqty__gt=0,
        ).only(
            "isbn", "title", "publisher", "price", "keywords", "description",
            "stockqty", "location", "minstocklimit", "coverimage",
        )

        for book in books:
            content_score = _cosine_like(profile, _book_tokens(book))
            global_score = global_scores.get(book.isbn, 0.0)
            seen_penalty = 0.08 if book.isbn in interacted_isbns else 0.0
            favorite_penalty = 0.10 if book.isbn in favorite_isbns else 0.0
            seed_bonus = 0.03 if book.isbn in candidate_isbns else 0.0
            total = (
                content_score * self.CONTENT_WEIGHT
                + global_score * (self.SALES_WEIGHT + self.RECENCY_WEIGHT)
                + seed_bonus * self.SEED_BOOK_WEIGHT
                - seen_penalty
                - favorite_penalty
            )
            ranked.append((book.isbn, total))

        ranked.sort(key=lambda item: item[1], reverse=True)
        ranked_isbns = [isbn for isbn, _ in ranked]

        # Fill with globally good books so the homepage always has enough pages.
        seen = set(ranked_isbns)
        for isbn in self._get_global_ranking():
            if isbn not in seen:
                ranked_isbns.append(isbn)
                seen.add(isbn)
            if len(ranked_isbns) >= max(limit, self.GLOBAL_POOL_LIMIT):
                break

        return self._books_from_ranked_isbns(ranked_isbns[:limit])

    def _build_user_profile(self) -> Tuple[Counter, Set[str], Set[str]]:
        profile = Counter()
        interacted_isbns: Set[str] = set()
        favorite_isbns: Set[str] = set()

        searches = SearchHistory.objects.filter(
            customer_id=self.customer_id
        ).only("keyword", "search_time")[:self.RECENT_SEARCH_LIMIT]

        for index, record in enumerate(searches):
            weight = 2.0 * self._position_decay(index)
            for token in _tokenize(record.keyword):
                profile[token] += weight

        browses = BrowseHistory.objects.filter(
            customer_id=self.customer_id
        ).select_related("isbn").only(
            "isbn__isbn", "isbn__title", "isbn__keywords", "isbn__description", "browse_time"
        )[:self.RECENT_BROWSE_LIMIT]

        for index, record in enumerate(browses):
            book = record.isbn
            interacted_isbns.add(book.isbn)
            weight = 3.0 * self._position_decay(index)
            for token, token_weight in _book_tokens(book).items():
                profile[token] += weight * token_weight

        favorites = BookFavorite.objects.filter(
            customer_id=self.customer_id
        ).select_related("isbn").only(
            "isbn__isbn", "isbn__title", "isbn__keywords", "isbn__description", "created_at"
        )[:self.RECENT_FAVORITE_LIMIT]

        for index, record in enumerate(favorites):
            book = record.isbn
            favorite_isbns.add(book.isbn)
            interacted_isbns.add(book.isbn)
            weight = 5.0 * self._position_decay(index)
            for token, token_weight in _book_tokens(book).items():
                profile[token] += weight * token_weight

        return Counter(dict(profile.most_common(self.PROFILE_TOKEN_LIMIT))), interacted_isbns, favorite_isbns

    @staticmethod
    def _position_decay(index: int) -> float:
        return 1 / (1 + index * 0.15)

    def _get_candidate_isbns(self, profile: Counter, browsed_isbns: Set[str]) -> Set[str]:
        tokens = [token for token, _ in profile.most_common(self.CANDIDATE_TOKEN_LIMIT)]
        query = Q()
        for token in tokens:
            query |= (
                Q(title__icontains=token)
                | Q(keywords__icontains=token)
                | Q(description__icontains=token)
            )

        candidate_isbns: Set[str] = set(browsed_isbns)
        if query:
            candidate_isbns.update(
                Book.objects.filter(query, stockqty__gt=0)
                .values_list("isbn", flat=True)[:self.CANDIDATE_BOOK_LIMIT]
            )

        candidate_isbns.update(self._get_global_ranking()[:200])
        return candidate_isbns

    def _get_global_score_map(self) -> Dict[str, float]:
        sales_scores = self._get_sales_scores()
        recency_scores = self._get_recency_scores()
        all_isbns = set(sales_scores) | set(recency_scores)
        return {
            isbn: sales_scores.get(isbn, 0.0) * self.SALES_WEIGHT
            + recency_scores.get(isbn, 0.0) * self.RECENCY_WEIGHT
            for isbn in all_isbns
        }

    def _get_global_ranking(self) -> List[str]:
        cached = cache.get(GLOBAL_RANKING_CACHE_KEY)
        if cached is not None:
            return cached

        global_scores = self._get_global_score_map()
        books = Book.objects.filter(stockqty__gt=0).only("isbn", "title")
        ranked = sorted(
            ((book.isbn, global_scores.get(book.isbn, 0.0), book.title) for book in books),
            key=lambda item: (item[1], item[2] or ""),
            reverse=True,
        )
        isbns = [isbn for isbn, _, _ in ranked[:self.GLOBAL_POOL_LIMIT]]
        cache.set(GLOBAL_RANKING_CACHE_KEY, isbns, GLOBAL_RANKING_CACHE_TIMEOUT)
        return isbns

    def _get_sales_scores(self) -> Dict[str, float]:
        scores = cache.get(SALES_CACHE_KEY)
        if scores is None:
            scores = self._calculate_sales_scores()
            cache.set(SALES_CACHE_KEY, scores, SALES_CACHE_TIMEOUT)
        return scores

    def _get_recency_scores(self) -> Dict[str, float]:
        scores = cache.get(RECENCY_CACHE_KEY)
        if scores is None:
            scores = self._calculate_recency_scores()
            cache.set(RECENCY_CACHE_KEY, scores, RECENCY_CACHE_TIMEOUT)
        return scores

    def _calculate_sales_scores(self) -> Dict[str, float]:
        sales_data = list(
            Orderdetail.objects.values("isbn").annotate(total_qty=Sum("quantity"))
        )
        if not sales_data:
            return {}

        quantities = [item["total_qty"] or 0 for item in sales_data]
        max_sales = max(quantities) or 1
        min_sales = min(quantities)
        sales_range = max(max_sales - min_sales, 1)
        return {
            item["isbn"]: ((item["total_qty"] or 0) - min_sales) / sales_range
            for item in sales_data
        }

    def _calculate_recency_scores(self) -> Dict[str, float]:
        cutoff_date = timezone.now() - timedelta(days=self.RECENCY_DAYS)
        recent_orders = list(
            Orderdetail.objects.filter(orderid__orderdate__gte=cutoff_date)
            .values("isbn")
            .annotate(recent_qty=Sum("quantity"), latest_date=Max("orderid__orderdate"))
        )
        if not recent_orders:
            return {}

        max_recent = max(item["recent_qty"] or 0 for item in recent_orders) or 1
        now = timezone.now()
        scores: Dict[str, float] = {}
        for item in recent_orders:
            latest_date = item["latest_date"] or now
            days_ago = max((now - latest_date).days, 0)
            decay = (1 - self.RECENCY_DECAY_RATE) ** days_ago
            scores[item["isbn"]] = ((item["recent_qty"] or 0) / max_recent) * decay
        return scores

    @staticmethod
    def _books_from_ranked_isbns(isbns: Sequence[str]) -> List[Book]:
        if not isbns:
            return []

        books = Book.objects.filter(isbn__in=isbns, stockqty__gt=0).only(
            "isbn", "title", "publisher", "price", "keywords", "description",
            "stockqty", "location", "minstocklimit", "coverimage",
        )
        book_dict = {book.isbn: book for book in books}
        return [book_dict[isbn] for isbn in isbns if isbn in book_dict]


def get_recommendations_for_user(customer_id: int, limit: int = 20) -> List[Book]:
    cache_key = f"user_recommendations_{customer_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return RecommendationEngine._books_from_ranked_isbns(cached[:limit])

    engine = RecommendationEngine(customer_id=customer_id)
    books = engine.get_recommendations(limit=RecommendationEngine.GLOBAL_POOL_LIMIT)
    isbn_list = [book.isbn for book in books]
    cache.set(cache_key, isbn_list, 300)
    return books[:limit]


def get_default_recommendations(limit: int = 20) -> List[Book]:
    cache_key = "default_recommendations"
    cached = cache.get(cache_key)
    if cached is not None:
        return RecommendationEngine._books_from_ranked_isbns(cached[:limit])

    engine = RecommendationEngine(customer_id=None)
    books = engine.get_recommendations(limit=RecommendationEngine.GLOBAL_POOL_LIMIT)
    isbn_list = [book.isbn for book in books]
    cache.set(cache_key, isbn_list, 300)
    return books[:limit]


def _feed_cache_key(customer_id: Optional[int], feed_key: str) -> str:
    if customer_id:
        return f"home_feed_user_{customer_id}"
    return f"home_feed_guest_{feed_key or 'default'}"


def invalidate_feed_cache(customer_id: Optional[int] = None, feed_key: Optional[str] = None) -> None:
    if customer_id is not None:
        cache.delete(_feed_cache_key(customer_id, ""))
    if feed_key is not None:
        cache.delete(_feed_cache_key(None, feed_key))


def build_home_feed_isbns(
    customer_id: Optional[int] = None,
    *,
    refresh: bool = False,
    feed_key: str = "default",
) -> List[str]:
    """
    首页 Feed：个性化/全局排序 + 随机探索，让长尾书也有机会出现。
    结果缓存在 Django cache，refresh=True 时重算并打乱前几屏。
    """
    cache_key = _feed_cache_key(customer_id, feed_key)
    if refresh:
        cache.delete(cache_key)
        if customer_id:
            cache.delete(f"user_recommendations_{customer_id}")
        else:
            cache.delete("default_recommendations")

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    engine = RecommendationEngine(customer_id=customer_id)
    ranked_isbns = [book.isbn for book in engine.get_recommendations(limit=FEED_RANKED_SIZE)]
    ranked_set = set(ranked_isbns)

    all_isbns = list(Book.objects.filter(stockqty__gt=0).values_list("isbn", flat=True))
    remainder = [isbn for isbn in all_isbns if isbn not in ranked_set]

    rng = random.Random(int(time.time()) if refresh else (hash(cache_key) % (2**32)))
    explore_count = min(FEED_EXPLORE_SIZE, len(remainder))
    explore_isbns = rng.sample(remainder, explore_count) if explore_count else []

    feed: List[str] = []
    ri, ei = 0, 0
    while ri < len(ranked_isbns) or ei < len(explore_isbns):
        for _ in range(3):
            if ri < len(ranked_isbns):
                feed.append(ranked_isbns[ri])
                ri += 1
        if ei < len(explore_isbns):
            feed.append(explore_isbns[ei])
            ei += 1

    seen: Set[str] = set()
    deduped: List[str] = []
    for isbn in feed:
        if isbn not in seen:
            seen.add(isbn)
            deduped.append(isbn)

    if refresh and len(deduped) > 12:
        head = deduped[:FEED_SHUFFLE_HEAD]
        rng.shuffle(head)
        deduped = head + deduped[FEED_SHUFFLE_HEAD:]

    cache.set(cache_key, deduped, FEED_CACHE_TIMEOUT)
    return deduped


def invalidate_recommendation_cache(customer_id: Optional[int] = None):
    if customer_id:
        cache.delete(f"user_recommendations_{customer_id}")
        invalidate_feed_cache(customer_id=customer_id)
        return

    cache.delete(SALES_CACHE_KEY)
    cache.delete(RECENCY_CACHE_KEY)
    cache.delete(GLOBAL_RANKING_CACHE_KEY)
    cache.delete("default_recommendations")
