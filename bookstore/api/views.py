"""
REST API 视图：每个类/方法与 Web views.py 中的函数对应关系见类 docstring。

统一响应格式：
  成功：{"success": true, ...}
  失败：{"success": false, "error": "..."}  + 合适 HTTP 状态码
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from bookstore.models import Book, Customer
from bookstore.views import _build_book_data

from .auth_tokens import create_token, revoke_token
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

class BookListView(APIView):
    """GET /api/books/  ←→  views.index"""

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        # 获取分页参数
        try:
            page = int(request.query_params.get("page", 1))
            if page < 1:
                page = 1
        except (ValueError, TypeError):
            page = 1

        page_size = int(request.query_params.get("page_size", 12))

        # 获取所有书籍
        all_books = Book.objects.all().order_by("title")
        total_count = all_books.count()
        total_pages = max(1, (total_count + page_size - 1) // page_size)

        # 确保页码有效
        if page > total_pages:
            page = total_pages

        # 分页
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_books = list(all_books[start_idx:end_idx])

        # 获取当前页书籍的 ISBN 列表
        page_isbns = [book.isbn for book in page_books]

        # 批量查询作者信息
        from bookstore.models import Bookauthor
        authors_list = Bookauthor.objects.filter(isbn__in=page_isbns).order_by('isbn', 'authororder')
        authors_dict = {}
        for author in authors_list:
            if author.isbn_id not in authors_dict:
                authors_dict[author.isbn_id] = []
            authors_dict[author.isbn_id].append(author.authorname)

        # 构建返回数据
        books_data = []
        for book in page_books:
            book_data = _build_book_data(book)
            book_data["price"] = str(book_data["price"])
            book_data["keywords"] = book_data["keywords"] or ""
            book_data["location"] = book_data["location"] or ""
            book_data["authors"] = " / ".join(authors_dict.get(book.isbn, []))
            books_data.append(book_data)

        return _ok(
            {
                "books": books_data,
                "default_cover_url": get_default_cover_url(),
                "current_page": page,
                "total_pages": total_pages,
                "total_count": total_count,
            }
        )


class BookSearchView(APIView):
    """GET /api/books/search/?q=  ←→  views.search"""

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        query = request.query_params.get("q", "")
        books = services.search_books(query)
        return _ok(
            {
                "query": query,
                "books": [serialize_book(b) for b in books],
            }
        )


class BookDetailView(APIView):
    """GET /api/books/<isbn>/  ←→  views.book_detail"""

    authentication_classes = []
    permission_classes = []

    def get(self, request, isbn):
        try:
            book = Book.objects.get(pk=isbn)
        except Book.DoesNotExist:
            return _err("图书不存在", status.HTTP_404_NOT_FOUND)
        return _ok(
            {
                "book": serialize_book(book, include_authors=True),
                "default_cover_url": get_default_cover_url(),
            }
        )


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
# 首页推荐书籍分页 API
# ---------------------------------------------------------------------------

def get_books_page(request):
    """
    GET /api/books/?page=1
    返回指定页的推荐书籍 - 优化版，解决N+1查询问题
    """
    from django.http import JsonResponse
    from django.core.cache import cache
    
    try:
        page = int(request.GET.get("page", 1))
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1
    
    page_size = 12
    
    # 根据用户是否登录获取不同的推荐 - 先从缓存获取ISBN列表
    customer_id = request.session.get("customer_id")
    cache_key = f'user_recommendations_{customer_id}' if customer_id else 'default_recommendations'
    isbn_list = cache.get(cache_key)
    
    if isbn_list is None:
        # 缓存未命中，重新计算
        if customer_id:
            from bookstore.recommendations import get_recommendations_for_user
            engine_books = get_recommendations_for_user(customer_id, limit=1000)
        else:
            from bookstore.recommendations import get_default_recommendations
            engine_books = get_default_recommendations(limit=1000)
        isbn_list = [b.isbn for b in engine_books]
        cache.set(cache_key, isbn_list, 300)  # 5分钟
    
    # 分页计算
    total_count = len(isbn_list)
    total_pages = max(1, (total_count + page_size - 1) // page_size)
    
    if page > total_pages:
        page = total_pages
    
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_isbns = isbn_list[start_idx:end_idx]
    
    if not page_isbns:
        return JsonResponse({
            'success': True,
            'books': [],
            'default_cover_url': None,
            'current_page': page,
            'total_pages': total_pages,
            'total_count': total_count,
        })
    
    # 批量查询书籍 - 使用in查询
    from bookstore.models import Book, Bookauthor
    books = Book.objects.filter(isbn__in=page_isbns)
    books_dict = {b.isbn: b for b in books}
    
    # 批量查询作者
    authors_list = Bookauthor.objects.filter(isbn__in=page_isbns).order_by('isbn', 'authororder')
    authors_dict = {}
    for author in authors_list:
        if author.isbn_id not in authors_dict:
            authors_dict[author.isbn_id] = []
        authors_dict[author.isbn_id].append(author.authorname)
    
    default_cover_url = get_default_cover_url()
    
    # 按原始顺序构建书籍数据
    books_data = []
    for isbn in page_isbns:
        book = books_dict.get(isbn)
        if not book:
            continue
        
        book_data = _build_book_data(book)
        book_data['price'] = str(book_data['price'])
        book_data['keywords'] = book_data['keywords'] or ''
        book_data['location'] = book_data['location'] or ''
        book_data['authors'] = ' / '.join(authors_dict.get(isbn, []))
        books_data.append(book_data)
    
    return JsonResponse({
        'success': True,
        'books': books_data,
        'default_cover_url': default_cover_url,
        'current_page': page,
        'total_pages': total_pages,
        'total_count': total_count,
    })
