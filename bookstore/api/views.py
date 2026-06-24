"""
REST API 视图：每个类/方法与 Web views.py 中的函数对应关系见类 docstring。

统一响应格式：
  成功：{"success": true, ...}
  失败：{"success": false, "error": "..."}  + 合适 HTTP 状态码
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from datetime import timedelta

from django.core.paginator import Paginator
from django.db.models import F, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone

from bookstore.models import Book, BookFavorite, Customer, FavoriteFolder, Orderdetail
from bookstore.views import (
    _build_book_data,
    _category_stats,
    _ensure_book_favorite_table,
    _favorite_folders_for_customer,
    _get_default_favorite_folder,
    _rank_book_data,
    _ranked_books_from_order_rows,
)

from .auth_tokens import create_token, revoke_token
from .authentication import CustomerTokenAuthentication
from .permissions import IsCustomer
from . import services
from .serializers import (
    default_cover_url as get_default_cover_url,
    serialize_account_summary,
    serialize_book,
    serialize_customer,
)


def _ok(data: dict, http_status=status.HTTP_200_OK) -> Response:
    return Response({"success": True, **data}, status=http_status)


def _err(message: str, http_status=status.HTTP_400_BAD_REQUEST) -> Response:
    return Response({"success": False, "error": message}, status=http_status)


def _customer_view(request) -> Customer:
    return request.user  # CustomerTokenAuthentication 将 Customer 赋给 request.user


def _api_book_payload(book: Book, **extra) -> dict:
    """将 _build_book_data 转为 APP 友好的 JSON（authors 为列表）。"""
    data = _build_book_data(book)
    authors_raw = data.get("authors") or ""
    authors = (
        [part.strip() for part in authors_raw.split(" / ") if part.strip()]
        if isinstance(authors_raw, str)
        else list(authors_raw or [])
    )
    payload = {
        "isbn": data["isbn"],
        "title": data["title"],
        "publisher": data.get("publisher"),
        "price": str(data["price"]),
        "keywords": data.get("keywords") or "",
        "stockqty": data["stockqty"],
        "location": data.get("location") or "",
        "minstocklimit": data["minstocklimit"],
        "cover_image_url": _app_cover_url(book.isbn),
        "coverimage": data.get("coverimage"),
        "authors": authors,
    }
    payload.update(extra)
    return payload


def _serialize_favorite_folder(folder: FavoriteFolder) -> dict:
    return {
        "id": folder.id,
        "name": folder.name,
        "is_default": bool(folder.is_default),
    }


def _app_cover_url(isbn: str) -> str:
    from bookstore.views import app_cover_url

    return app_cover_url(isbn)


def _default_cover_file():
    from django.conf import settings

    subdir = getattr(settings, "COVER_IMAGE_SUBDIR", "images")
    filename = getattr(settings, "DEFAULT_COVER_IMAGE_FILENAME", "default_cover.png")
    path = settings.BASE_DIR / "static" / subdir / filename
    if not path.exists():
        path = settings.BASE_DIR / "static" / "images" / "default_cover.png"
    return path


def _cover_cache_headers() -> dict:
    return {"Cache-Control": "public, max-age=86400"}


class BookCoverView(APIView):
    """GET /api/books/<isbn>/cover/  — 封面代理（外链失败时返回本地默认图）。"""

    authentication_classes = []
    permission_classes = []

    def get(self, request, isbn):
        import base64
        from django.conf import settings as dj_settings
        from django.http import FileResponse, HttpResponse

        from bookstore.views import (
            _resolve_cover_backend_sources,
            fetch_external_cover_bytes,
            get_book_cover_image,
        )

        try:
            book = Book.objects.get(pk=isbn)
        except Book.DoesNotExist:
            return FileResponse(
                _default_cover_file().open("rb"),
                content_type="image/png",
                headers=_cover_cache_headers(),
            )

        external, cover_b64 = _resolve_cover_backend_sources(book)

        if external and external.startswith("/static/"):
            rel = external[len("/static/") :]
            local = dj_settings.BASE_DIR / "static" / rel
            if local.exists():
                return FileResponse(
                    local.open("rb"),
                    content_type="image/jpeg",
                    headers=_cover_cache_headers(),
                )

        if external and external.startswith(("http://", "https://")):
            fetched = fetch_external_cover_bytes(external)
            if fetched:
                body, ctype = fetched
                return HttpResponse(body, content_type=ctype, headers=_cover_cache_headers())

        if cover_b64:
            try:
                body = base64.b64decode(cover_b64)
                if body:
                    return HttpResponse(body, content_type="image/jpeg", headers=_cover_cache_headers())
            except (ValueError, TypeError):
                pass

        static_path = get_book_cover_image(book.title)
        if static_path.startswith("/static/"):
            rel = static_path[len("/static/") :]
            local = dj_settings.BASE_DIR / "static" / rel
            if local.exists():
                return FileResponse(
                    local.open("rb"),
                    content_type="image/jpeg",
                    headers=_cover_cache_headers(),
                )

        return FileResponse(
            _default_cover_file().open("rb"),
            content_type="image/png",
            headers=_cover_cache_headers(),
        )


# ---------------------------------------------------------------------------
# 认证 — 对应 customer_login / customer_register / customer_logout
# ---------------------------------------------------------------------------

class LoginView(APIView):
    """POST /api/auth/login/  ←→  views.customer_login"""

    authentication_classes = []  # 登录接口无需 Token
    permission_classes = []

    def post(self, request):
        username = request.data.get("username", "")
        password = request.data.get("password", "")
        ok, result = services.login_customer(username, password)
        if not ok:
            return _err(result["error"], status.HTTP_401_UNAUTHORIZED)
        customer = result["customer"]
        token = create_token(customer.customerid)
        return _ok(
            {
                "message": result["message"],
                "token": token,
                "customer": serialize_customer(customer),
            }
        )


class RegisterView(APIView):
    """POST /api/auth/register/  ←→  views.customer_register"""

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        ok, result = services.register_customer(request.data)
        if not ok:
            return _err(result["error"])
        customer = result["customer"]
        token = create_token(customer.customerid)
        return _ok(
            {
                "message": result["message"],
                "token": token,
                "customer": serialize_customer(customer),
            },
            status.HTTP_201_CREATED,
        )


class LogoutView(APIView):
    """POST /api/auth/logout/  ←→  views.customer_logout"""

    permission_classes = [IsCustomer]

    def post(self, request):
        token = request.auth
        if token:
            revoke_token(token)
        return _ok({"message": "您已退出登录"})


class MeView(APIView):
    """GET /api/auth/me/  — 当前登录用户信息（Web 无独立页，合并 account 摘要）"""

    permission_classes = [IsCustomer]

    def get(self, request):
        customer = _customer_view(request)
        return _ok({"customer": serialize_account_summary(customer)})


# ---------------------------------------------------------------------------
# 图书 — 对应 index / book_detail / search
# ---------------------------------------------------------------------------

def _resolve_customer_id(request) -> Optional[int]:
    user = getattr(request, "user", None)
    if user is not None and hasattr(user, "customerid"):
        return user.customerid
    return request.session.get("customer_id")


def _books_payload_for_isbns(page_isbns: list) -> list:
    from bookstore.models import Bookauthor

    if not page_isbns:
        return []

    books = Book.objects.filter(isbn__in=page_isbns)
    books_dict = {b.isbn: b for b in books}

    authors_list = Bookauthor.objects.filter(isbn__in=page_isbns).order_by("isbn", "authororder")
    authors_dict: dict = {}
    for author in authors_list:
        authors_dict.setdefault(author.isbn_id, []).append(author.authorname)

    books_data = []
    for isbn in page_isbns:
        book = books_dict.get(isbn)
        if not book:
            continue
        book_data = _build_book_data(book)
        book_data["price"] = str(book_data["price"])
        book_data["keywords"] = book_data["keywords"] or ""
        book_data["location"] = book_data["location"] or ""
        book_data["authors"] = authors_dict.get(isbn, [])
        book_data["cover_image_url"] = _app_cover_url(isbn)
        book_data["coverimage"] = None
        books_data.append(book_data)
    return books_data


class BookListView(APIView):
    """GET /api/books/  — 首页推荐 Feed（无限滚动 + refresh 换一批）"""

    authentication_classes = [CustomerTokenAuthentication]
    permission_classes = []

    def get(self, request):
        try:
            page = int(request.query_params.get("page", 1))
            if page < 1:
                page = 1
        except (ValueError, TypeError):
            page = 1

        try:
            page_size = int(request.query_params.get("page_size", 12))
            page_size = max(1, min(page_size, 48))
        except (ValueError, TypeError):
            page_size = 12

        refresh = request.query_params.get("refresh", "").lower() in ("1", "true", "yes")
        customer_id = _resolve_customer_id(request)
        feed_key = request.session.session_key or "default"

        from bookstore.recommendations import build_home_feed_isbns

        isbn_list = build_home_feed_isbns(
            customer_id=customer_id,
            refresh=refresh,
            feed_key=feed_key,
        )

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_isbns = isbn_list[start_idx:end_idx]
        has_more = end_idx < len(isbn_list)

        return _ok(
            {
                "books": _books_payload_for_isbns(page_isbns),
                "default_cover_url": get_default_cover_url(),
                "has_more": has_more,
            }
        )


class BookSearchView(APIView):
    """GET /api/books/search/?q=  ←→  views.search"""

    authentication_classes = [CustomerTokenAuthentication]
    permission_classes = []

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        customer = request.user if isinstance(request.user, Customer) else None

        if not query:
            recent_searches = []
            if customer:
                from bookstore.tracking import get_recent_search_keywords

                recent_searches = get_recent_search_keywords(customer.customerid)
            return _ok({"query": "", "books": [], "recent_searches": recent_searches})

        books = services.search_books(query)
        if customer:
            from bookstore.tracking import record_search

            record_search(customer.customerid, query)
        books_data = []
        for book in books:
            item = serialize_book(book)
            item["cover_image_url"] = _app_cover_url(book.isbn)
            books_data.append(item)
        return _ok(
            {
                "query": query,
                "books": books_data,
                "recent_searches": [],
            }
        )


class SearchHistoryClearView(APIView):
    """DELETE /api/books/search/history/  — 清除最近搜索"""

    permission_classes = [IsCustomer]

    def delete(self, request):
        customer = _customer_view(request)
        from bookstore.tracking import clear_search_history

        clear_search_history(customer.customerid)
        return _ok({"message": "已清除搜索历史", "recent_searches": []})


class BookDetailView(APIView):
    """GET /api/books/<isbn>/  ←→  views.book_detail"""

    authentication_classes = [CustomerTokenAuthentication]
    permission_classes = []

    def get(self, request, isbn):
        try:
            book = Book.objects.get(pk=isbn)
        except Book.DoesNotExist:
            return _err("图书不存在", status.HTTP_404_NOT_FOUND)

        payload = {
            "book": serialize_book(book, include_authors=True),
            "default_cover_url": get_default_cover_url(),
        }
        payload["book"]["cover_image_url"] = _app_cover_url(isbn)
        if isinstance(request.user, Customer):
            customer_id = request.user.customerid
            from bookstore.tracking import record_browse

            record_browse(customer_id, isbn)
            _ensure_book_favorite_table()
            favorite = BookFavorite.objects.filter(customer_id=customer_id, isbn_id=isbn).first()
            folders = _favorite_folders_for_customer(customer_id)
            payload.update(
                {
                    "is_favorited": favorite is not None,
                    "favorite_count": BookFavorite.objects.filter(isbn_id=isbn).count(),
                    "favorite_folder_id": favorite.folder_id if favorite else None,
                    "favorite_folders": [_serialize_favorite_folder(f) for f in folders],
                }
            )
        return _ok(payload)


# ---------------------------------------------------------------------------
# 购物车 — 对应 cart_detail / cart_add / cart_update / cart_remove
# ---------------------------------------------------------------------------

class CartView(APIView):
    """GET /api/cart/  ←→  views.cart_detail"""

    permission_classes = [IsCustomer]

    def get(self, request):
        customer = _customer_view(request)
        return _ok({"cart": services.build_cart_payload(customer.customerid)})


class CartItemView(APIView):
    """
    POST   /api/cart/items/          body: {isbn, quantity}  ←→  cart_add
    PUT    /api/cart/items/<isbn>/   body: {quantity}        ←→  cart_update
    DELETE /api/cart/items/<isbn>/                           ←→  cart_remove
    """

    permission_classes = [IsCustomer]

    def post(self, request):
        customer = _customer_view(request)
        isbn = request.data.get("isbn")
        if not isbn:
            return _err("缺少 isbn")
        try:
            quantity = int(request.data.get("quantity", 1))
        except (TypeError, ValueError):
            quantity = 1
        result = services.add_to_cart(customer.customerid, isbn, quantity)
        return _ok(result)

    def put(self, request, isbn):
        customer = _customer_view(request)
        try:
            quantity = int(request.data.get("quantity", 0))
        except (TypeError, ValueError):
            return _err("请输入有效的数量")
        result = services.update_cart_item(customer.customerid, isbn, quantity)
        return _ok(result)

    def delete(self, request, isbn):
        customer = _customer_view(request)
        result = services.remove_from_cart(customer.customerid, isbn)
        return _ok(result)


# ---------------------------------------------------------------------------
# 订单 — 对应 order_confirm / order_list / order_detail / pay / cancel / confirm_receipt
# ---------------------------------------------------------------------------

class OrderPreviewView(APIView):
    """GET /api/orders/preview/  ←→  views.order_confirm GET"""

    permission_classes = [IsCustomer]

    def get(self, request):
        customer = _customer_view(request)
        preview = services.build_order_preview(customer.customerid)
        if preview.get("empty"):
            return _err(preview["message"])
        return _ok({"preview": preview})


class OrderListCreateView(APIView):
    """
    GET  /api/orders/  ←→  views.order_list
    POST /api/orders/  ←→  views.order_confirm POST
    """

    permission_classes = [IsCustomer]

    def get(self, request):
        customer = _customer_view(request)
        return _ok({"orders": services.list_orders(customer)})

    def post(self, request):
        customer = _customer_view(request)
        ok, result = services.create_order(
            customer,
            payment_choice=request.data.get("payment_choice", "balance"),
            shipping_name=request.data.get("shipping_name"),
            shipping_contact=request.data.get("shipping_contact"),
            shipping_address=request.data.get("shipping_address"),
        )
        if not ok:
            return _err(result.get("error", "下单失败"))
        return _ok(result, status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    """GET /api/orders/<id>/  ←→  views.order_detail"""

    permission_classes = [IsCustomer]

    def get(self, request, order_id):
        customer = _customer_view(request)
        order = services.get_order(customer, order_id)
        if order is None:
            return _err("订单不存在", status.HTTP_404_NOT_FOUND)
        return _ok({"order": order})


class OrderPayView(APIView):
    """POST /api/orders/<id>/pay/  ←→  views.pay_order"""

    permission_classes = [IsCustomer]

    def post(self, request, order_id):
        customer = _customer_view(request)
        ok, result = services.pay_order_remainder(customer, order_id)
        if not ok:
            return _err(result.get("error", "支付失败"))
        return _ok(result)


class OrderCancelView(APIView):
    """POST /api/orders/<id>/cancel/  ←→  views.cancel_order"""

    permission_classes = [IsCustomer]

    def post(self, request, order_id):
        customer = _customer_view(request)
        ok, result = services.cancel_order(customer, order_id)
        if not ok:
            return _err(result.get("error", "无法取消"))
        return _ok(result)


class OrderConfirmReceiptView(APIView):
    """POST /api/orders/<id>/confirm-receipt/  ←→  views.confirm_receipt"""

    permission_classes = [IsCustomer]

    def post(self, request, order_id):
        customer = _customer_view(request)
        ok, result = services.confirm_receipt(customer, order_id)
        if not ok:
            return _err(result.get("error", "无法确认收货"))
        return _ok(result)


# ---------------------------------------------------------------------------
# 账户 — 对应 account_recharge / account_edit / repay_overdraft
# ---------------------------------------------------------------------------

class AccountView(APIView):
    """
    GET   /api/account/  ←→  views.account_recharge GET（账户摘要）
    PATCH /api/account/  ←→  views.account_edit
    """

    permission_classes = [IsCustomer]

    def get(self, request):
        customer = _customer_view(request)
        # 刷新以获取最新余额
        customer = Customer.objects.select_related("levelid").get(pk=customer.customerid)
        return _ok({"account": serialize_account_summary(customer)})

    def patch(self, request):
        customer = _customer_view(request)
        ok, result = services.update_account(customer, request.data)
        if not ok:
            return _err(result["error"])
        return _ok(
            {
                "message": result["message"],
                "account": serialize_account_summary(result["customer"]),
            }
        )


class AccountRechargeView(APIView):
    """POST /api/account/recharge/  body: {amount}  ←→  views.account_recharge POST"""

    permission_classes = [IsCustomer]

    def post(self, request):
        customer = _customer_view(request)
        try:
            amount = Decimal(str(request.data.get("amount", "0")))
        except (InvalidOperation, TypeError):
            return _err("请输入有效的金额")
        ok, result = services.recharge_account(customer, amount)
        if not ok:
            return _err(result["error"])
        return _ok(
            {
                "message": result["message"],
                "account": serialize_account_summary(result["customer"]),
            }
        )


class AccountRepayView(APIView):
    """POST /api/account/repay/  ←→  views.repay_overdraft POST"""

    permission_classes = [IsCustomer]

    def post(self, request):
        customer = _customer_view(request)
        ok, result = services.repay_all_overdraft(customer)
        if not ok:
            return _err(result.get("error", "还款失败"))
        return _ok(
            {
                "message": result["message"],
                "account": serialize_account_summary(result["customer"]),
            }
        )


# ---------------------------------------------------------------------------
# AI 助手 — 对应 ai_chat / ai_chat_api / ai_chat_clear
# ---------------------------------------------------------------------------

class AiChatView(APIView):
    """GET /api/ai/  获取配置状态与历史；POST /api/ai/chat/  发送消息。"""

    permission_classes = [IsCustomer]

    def get(self, request):
        from bookstore.ai_service import is_ai_configured
        from bookstore.ai_chat_store import get_ai_history

        customer = _customer_view(request)
        return _ok(
            {
                "ai_configured": is_ai_configured(),
                "history": get_ai_history(customer.customerid),
            }
        )

    def post(self, request):
        from bookstore.ai_chat_store import get_ai_history, save_ai_history
        from bookstore.ai_service import chat_with_ai, AIServiceError

        user_message = (request.data.get("message") or "").strip()
        if not user_message:
            return _err("请输入消息。")

        customer = _customer_view(request)
        history = get_ai_history(customer.customerid)

        try:
            reply = chat_with_ai(history, user_message)
        except AIServiceError as exc:
            return _err(str(exc))
        except Exception:
            return _err("服务器内部错误，请稍后再试。", status.HTTP_500_INTERNAL_SERVER_ERROR)

        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": reply})
        save_ai_history(customer.customerid, history)

        return _ok({"reply": reply})


class AiClearView(APIView):
    """POST /api/ai/clear/  ←→  views.ai_chat_clear"""

    permission_classes = [IsCustomer]

    def post(self, request):
        from bookstore.ai_chat_store import clear_ai_history

        customer = _customer_view(request)
        clear_ai_history(customer.customerid)
        return _ok({"message": "对话已清空"})


# ---------------------------------------------------------------------------
# 分区 / 榜单 / 收藏 — 对应 categories / rankings / favorite_*
# ---------------------------------------------------------------------------

class CategoryListView(APIView):
    """GET /api/categories/  ←→  views.categories"""

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        selected_category = request.query_params.get("category", "").strip()
        sort = request.query_params.get("sort", "title")
        try:
            page = max(1, int(request.query_params.get("page", 1)))
        except (ValueError, TypeError):
            page = 1
        try:
            page_size = min(48, max(1, int(request.query_params.get("page_size", 12))))
        except (ValueError, TypeError):
            page_size = 12

        books = Book.objects.filter(stockqty__gt=0)
        if selected_category:
            books = books.filter(keywords__icontains=selected_category)

        sort_options = {
            "title": "title",
            "price_asc": "price",
            "price_desc": "-price",
            "stock_desc": "-stockqty",
        }
        books = books.order_by(sort_options.get(sort, "title"))

        paginator = Paginator(books, page_size)
        page_obj = paginator.get_page(page)
        books_data = [_api_book_payload(book) for book in page_obj.object_list]

        categories_data = _category_stats()
        for item in categories_data:
            item["active"] = item["name"] == selected_category

        return _ok(
            {
                "categories": categories_data,
                "books": books_data,
                "selected_category": selected_category,
                "sort": sort,
                "default_cover_url": get_default_cover_url(),
                "current_page": page_obj.number,
                "total_pages": paginator.num_pages,
                "total_count": paginator.count,
            }
        )


class RankingsView(APIView):
    """GET /api/rankings/  ←→  views.rankings"""

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        recent_cutoff = timezone.now() - timedelta(days=30)

        best_seller_rows = (
            Orderdetail.objects.values("isbn")
            .annotate(total_sales=Sum("quantity"))
            .order_by("-total_sales")[:20]
        )
        recent_hot_rows = (
            Orderdetail.objects.filter(orderid__orderdate__gte=recent_cutoff)
            .values("isbn")
            .annotate(recent_sales=Sum("quantity"))
            .order_by("-recent_sales")[:20]
        )
        low_stock = Book.objects.filter(
            stockqty__gt=0, stockqty__lte=F("minstocklimit")
        ).order_by("stockqty", "title")[:10]
        rich_descriptions = (
            Book.objects.filter(stockqty__gt=0)
            .exclude(description__isnull=True)
            .exclude(description="")
            .order_by("title")[:10]
        )

        def _section_books(raw_books):
            result = []
            for item in raw_books:
                result.append(
                    {
                        **item,
                        "price": str(item["price"]),
                        "keywords": item.get("keywords") or "",
                        "location": item.get("location") or "",
                        "authors": [
                            p.strip()
                            for p in (item.get("authors") or "").split(" / ")
                            if p.strip()
                        ],
                        "cover_image_url": _app_cover_url(item["isbn"]),
                    }
                )
            return result

        sections = [
            {
                "title": "畅销榜",
                "subtitle": "按历史订单销量排序，适合作为热门采购参考。",
                "icon": "local_fire_department",
                "books": _section_books(
                    _ranked_books_from_order_rows(best_seller_rows, "total_sales", "销量")[:10]
                ),
            },
            {
                "title": "近30天热销",
                "subtitle": "观察最近一段时间更受欢迎的图书。",
                "icon": "trending_up",
                "books": _section_books(
                    _ranked_books_from_order_rows(recent_hot_rows, "recent_sales", "近30天销量")[:10]
                ),
            },
            {
                "title": "库存紧俏",
                "subtitle": "库存低于预警线的图书，适合提醒补货或优先下单。",
                "icon": "inventory_2",
                "books": [
                    _api_book_payload(book, metric_label="库存", metric_value=book.stockqty)
                    for book in low_stock
                ],
            },
            {
                "title": "有简介可读",
                "subtitle": "优先展示已有简介的图书，方便用户做购买判断。",
                "icon": "menu_book",
                "books": [
                    _api_book_payload(book, metric_label="库存", metric_value=book.stockqty)
                    for book in rich_descriptions
                ],
            },
        ]
        return _ok({"sections": sections, "default_cover_url": get_default_cover_url()})


class BookFavoriteToggleView(APIView):
    """POST /api/books/<isbn>/favorite/  ←→  views.favorite_toggle"""

    permission_classes = [IsCustomer]

    def post(self, request, isbn):
        customer = _customer_view(request)
        get_object_or_404(Book, pk=isbn)
        _ensure_book_favorite_table()

        favorite = BookFavorite.objects.filter(
            customer_id=customer.customerid, isbn_id=isbn
        ).first()
        if favorite:
            favorite.delete()
            is_favorited = False
            message = "已取消收藏"
            folder_id = None
        else:
            requested_folder_id = request.data.get("folder_id")
            folder = None
            if requested_folder_id:
                folder = FavoriteFolder.objects.filter(
                    id=requested_folder_id, customer_id=customer.customerid
                ).first()
            if folder is None:
                folder = _get_default_favorite_folder(customer.customerid)

            BookFavorite.objects.create(
                customer_id=customer.customerid, isbn_id=isbn, folder=folder
            )
            is_favorited = True
            folder_id = folder.id
            message = f"已加入「{folder.name}」"

        from bookstore.recommendations import invalidate_recommendation_cache

        invalidate_recommendation_cache(customer_id=customer.customerid)
        return _ok(
            {
                "message": message,
                "is_favorited": is_favorited,
                "favorite_count": BookFavorite.objects.filter(isbn_id=isbn).count(),
                "folder_id": folder_id,
            }
        )


class FavoriteFolderListView(APIView):
    """GET/POST /api/favorites/folders/  ←→  views.favorite_folders"""

    permission_classes = [IsCustomer]

    def get(self, request):
        customer = _customer_view(request)
        _ensure_book_favorite_table()
        folders = list(_favorite_folders_for_customer(customer.customerid))
        folder_ids = [folder.id for folder in folders]
        favorites = BookFavorite.objects.filter(
            customer_id=customer.customerid,
            folder_id__in=folder_ids,
        ).select_related("isbn").order_by("folder_id", "-created_at")

        favorite_map = {folder.id: [] for folder in folders}
        for favorite in favorites:
            favorite_map.setdefault(favorite.folder_id, []).append(
                _api_book_payload(favorite.isbn)
            )

        folder_cards = []
        total_count = 0
        for folder in folders:
            books = favorite_map.get(folder.id, [])
            total_count += len(books)
            folder_cards.append(
                {
                    "folder": _serialize_favorite_folder(folder),
                    "books": books,
                    "count": len(books),
                }
            )

        return _ok({"folders": folder_cards, "total_count": total_count})

    def post(self, request):
        customer = _customer_view(request)
        _ensure_book_favorite_table()
        name = (request.data.get("name") or "").strip()
        if not name:
            return _err("收藏夹名称不能为空")
        if len(name) > 60:
            return _err("收藏夹名称不能超过60个字符")
        if FavoriteFolder.objects.filter(customer_id=customer.customerid, name=name).exists():
            return _err("该收藏夹名称已存在")

        folder = FavoriteFolder.objects.create(
            customer_id=customer.customerid, name=name, is_default=0
        )
        return _ok(
            {
                "message": f"收藏夹「{name}」创建成功",
                "folder": _serialize_favorite_folder(folder),
            },
            status.HTTP_201_CREATED,
        )


class FavoriteFolderDeleteView(APIView):
    """DELETE /api/favorites/folders/<folder_id>/  ←→  views.favorite_folder_delete"""

    permission_classes = [IsCustomer]

    def delete(self, request, folder_id):
        customer = _customer_view(request)
        _ensure_book_favorite_table()
        folder = get_object_or_404(
            FavoriteFolder, pk=folder_id, customer_id=customer.customerid
        )
        if folder.is_default:
            return _err("默认收藏夹不能删除", status.HTTP_400_BAD_REQUEST)

        folder_name = folder.name
        BookFavorite.objects.filter(customer_id=customer.customerid, folder=folder).delete()
        folder.delete()

        from bookstore.recommendations import invalidate_recommendation_cache

        invalidate_recommendation_cache(customer_id=customer.customerid)
        return _ok({"message": f"收藏夹「{folder_name}」已删除"})


class BrowseHistoryView(APIView):
    """GET /api/account/browse-history/  ←→  views.browse_history"""

    permission_classes = [IsCustomer]

    def get(self, request):
        customer = _customer_view(request)
        from bookstore.tracking import get_recent_browsed_isbns

        isbn_list = get_recent_browsed_isbns(customer.customerid)
        books = []
        for isbn in isbn_list:
            book = Book.objects.filter(pk=isbn).first()
            if book:
                item = serialize_book(book, include_authors=True)
                item["cover_image_url"] = _app_cover_url(book.isbn)
                books.append(item)
        return _ok({"books": books, "default_cover_url": get_default_cover_url()})


# ---------------------------------------------------------------------------
# 首页推荐书籍分页 API（已由 BookListView 统一处理，保留别名便于旧链接）
# ---------------------------------------------------------------------------

def get_books_page(request):
    """Deprecated: use BookListView at /api/books/ instead."""
    view = BookListView.as_view()
    return view(request)
