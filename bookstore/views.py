import json

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, F, Sum
from django.db import transaction, connection
from django.core.paginator import Paginator

from .models import Book, Bookauthor, Customer, Orders, Orderdetail, Creditlevel, BookFavorite, FavoriteFolder
from .cart_store import get_cart, save_cart, clear_cart
from .ai_chat_store import attach_customer_ai_history
from decimal import Decimal
from functools import wraps
from datetime import timedelta


def customer_login(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        try:
            customer = Customer.objects.get(username=username, password=password)
            request.session["customer_id"] = customer.customerid
            request.session["customer_name"] = customer.name
            attach_customer_ai_history(request, customer.customerid)
            messages.success(request, "登录成功")
            return redirect("bookstore:index")
        except Customer.DoesNotExist:
            messages.error(request, "用户名或密码错误")

    return render(request, "bookstore/login.html")
    

def customer_register(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        address = request.POST.get("address", "").strip()

        # 验证输入
        if not username or not password or not name or not email:
            messages.error(request, "所有字段都是必填的")
            return render(request, "bookstore/register.html")

        if password != confirm_password:
            messages.error(request, "两次输入的密码不一致")
            return render(request, "bookstore/register.html")

        if len(password) < 6:
            messages.error(request, "密码长度至少6位")
            return render(request, "bookstore/register.html")

        # 检查用户名是否已存在
        if Customer.objects.filter(username=username).exists():
            messages.error(request, "用户名已存在")
            return render(request, "bookstore/register.html")

        # 检查邮箱是否已存在
        if Customer.objects.filter(email=email).exists():
            messages.error(request, "邮箱已被注册")
            return render(request, "bookstore/register.html")

        try:
            from django.utils import timezone
            # 创建新用户
            customer = Customer.objects.create(
                username=username,
                password=password,  # 注意：生产环境中应该加密密码
                name=name,
                email=email,
                address=address,
                balance=Decimal('0.00'),
                levelid_id=1,  # 默认1级会员
                creditlimit=Decimal('0.00'),  # 1级无信用额度
                usedcredit=Decimal('0.00'),
                totalspent=Decimal('0.00'),
                registerdate=timezone.now()  # 显式设置注册时间
            )

            # 自动登录新用户
            request.session["customer_id"] = customer.customerid
            request.session["customer_name"] = customer.name
            attach_customer_ai_history(request, customer.customerid)

            messages.success(request, f"注册成功！欢迎加入，{customer.name}")
            return redirect("bookstore:index")

        except Exception as e:
            messages.error(request, f"注册失败：{e}")
            return render(request, "bookstore/register.html")

    return render(request, "bookstore/register.html")


def customer_logout(request: HttpRequest) -> HttpResponse:
    request.session.pop("customer_id", None)
    request.session.pop("customer_name", None)
    request.session.pop("ai_chat_history", None)
    messages.info(request, "您已退出登录")
    return redirect("bookstore:index")


def customer_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if "customer_id" not in request.session:
            messages.warning(request, "请先登录顾客账户")
            return redirect("bookstore:login")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def get_book_cover_image(book_title: str) -> str:
    """
    根据书名返回对应的封面图片路径。
    如果没有匹配，返回默认封面图片。
    """
    title_lower = book_title.lower()

    # 从 settings 中读取映射与目录，保持可配置性
    from django.conf import settings
    from urllib.parse import quote
    image_mappings = getattr(settings, "COVER_IMAGE_MAPPINGS", {})
    images_subdir = getattr(settings, "COVER_IMAGE_SUBDIR", "images")
    default_prefix = settings.STATIC_URL if settings.STATIC_URL.endswith('/') else settings.STATIC_URL + '/'
    default_filename = getattr(settings, "DEFAULT_COVER_IMAGE_FILENAME", "default_cover.png")

    # 查找匹配的关键词并构建静态 URL（对文件名进行 URL 编码以支持中文）
    for keyword, image_filename in image_mappings.items():
        if keyword in title_lower:
            return f"{default_prefix}{images_subdir}/{quote(image_filename)}"

    # 如果没有匹配的关键词，返回默认封面图片
    return f"{default_prefix}{images_subdir}/{quote(default_filename)}"


def _default_cover_url() -> str:
    return get_book_cover_image("")


def _build_book_data(book):
    """构建书籍数据字典，包含封面图片处理"""
    # 查询该书的作者，按序位排序后用 / 拼接
    authors = Bookauthor.objects.filter(isbn=book).order_by('authororder')
    author_names = ' / '.join([a.authorname for a in authors])

    book_data = {
        'isbn': book.isbn,
        'title': book.title,
        'publisher': book.publisher,
        'price': book.price,
        'keywords': book.keywords,
        'stockqty': book.stockqty,
        'location': book.location,
        'minstocklimit': book.minstocklimit,
        'coverimage': None,
        'cover_image_url': None,
        'authors': author_names,
    }

    # 优先使用数据库中的URL封面
    if book.coverimage:
        cover_url = book.coverimage
        # 处理 bytes 格式 (b'...') 和字符串格式
        if isinstance(cover_url, bytes):
            try:
                cover_url = cover_url.decode('utf-8')
            except:
                cover_url = None
        elif isinstance(cover_url, str):
            # 清理 bytes 格式字符串 b'...' 或 b"..."
            if cover_url.startswith("b'") and cover_url.endswith("'"):
                cover_url = cover_url[2:-1]
            elif cover_url.startswith('b"') and cover_url.endswith('"'):
                cover_url = cover_url[2:-1]
        
        # 验证是否为有效的URL
        if cover_url and (cover_url.startswith('http://') or cover_url.startswith('https://')):
            book_data['cover_image_url'] = cover_url
    # 如果没有URL图片，则尝试使用静态图片文件
    if not book_data['cover_image_url']:
        static_image = get_book_cover_image(book.title)
        if static_image:
            book_data['cover_image_url'] = static_image

    return book_data


def index(request: HttpRequest) -> HttpResponse:
    from django.conf import settings
    from urllib.parse import quote

    page_size = 12
    customer_id = request.session.get("customer_id")
    feed_key = request.session.session_key or "default"

    from .recommendations import RecommendationEngine, build_home_feed_isbns

    isbn_list = build_home_feed_isbns(
        customer_id=customer_id,
        refresh=False,
        feed_key=feed_key,
    )
    page_isbns = isbn_list[:page_size]
    page_books = RecommendationEngine._books_from_ranked_isbns(page_isbns)
    books_with_covers = [_build_book_data(book) for book in page_books]

    default_filename = getattr(settings, "DEFAULT_COVER_IMAGE_FILENAME", "Python编程从入门到实践.jpg")
    images_subdir = getattr(settings, "COVER_IMAGE_SUBDIR", "images")
    static_prefix = settings.STATIC_URL if settings.STATIC_URL.endswith('/') else settings.STATIC_URL + '/'
    default_cover_url = f"{static_prefix}{images_subdir}/{quote(default_filename)}"

    return render(request, "bookstore/index.html", {
        "books": books_with_covers,
        "DEFAULT_COVER_IMAGE_URL": default_cover_url,
        "has_more_initial": len(isbn_list) > page_size,
    })


def _split_keywords(keywords: str) -> list[str]:
    if not keywords:
        return []
    return [kw.strip() for kw in keywords.replace("，", ",").split(",") if kw.strip()]


def _category_stats(limit: int = 24) -> list[dict]:
    counts = {}
    for keywords in Book.objects.filter(stockqty__gt=0).exclude(keywords__isnull=True).values_list("keywords", flat=True):
        for keyword in _split_keywords(keywords):
            counts[keyword] = counts.get(keyword, 0) + 1
    return [
        {"name": name, "count": count}
        for name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]
    ]


def categories(request: HttpRequest) -> HttpResponse:
    """书籍分区浏览页：按关键词聚合成商城式分类入口。"""
    selected_category = request.GET.get("category", "").strip()
    sort = request.GET.get("sort", "title")
    page_number = request.GET.get("page", 1)

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

    paginator = Paginator(books, 12)
    page_obj = paginator.get_page(page_number)
    books_with_covers = [_build_book_data(book) for book in page_obj.object_list]

    categories_data = _category_stats()
    for item in categories_data:
        item["active"] = item["name"] == selected_category

    from django.conf import settings
    from urllib.parse import quote
    default_filename = getattr(settings, "DEFAULT_COVER_IMAGE_FILENAME", "Python编程从入门到实践.jpg")
    images_subdir = getattr(settings, "COVER_IMAGE_SUBDIR", "images")
    static_prefix = settings.STATIC_URL if settings.STATIC_URL.endswith('/') else settings.STATIC_URL + '/'
    default_cover_url = f"{static_prefix}{images_subdir}/{quote(default_filename)}"

    return render(request, "bookstore/categories.html", {
        "categories": categories_data,
        "books": books_with_covers,
        "page_obj": page_obj,
        "selected_category": selected_category,
        "sort": sort,
        "DEFAULT_COVER_IMAGE_URL": default_cover_url,
    })


def _rank_book_data(book, metric_label: str, metric_value) -> dict:
    data = _build_book_data(book)
    data["metric_label"] = metric_label
    data["metric_value"] = metric_value if metric_value is not None else 0
    return data


def _ranked_books_from_order_rows(rows, metric_key: str, metric_label: str) -> list[dict]:
    rows = list(rows)
    isbns = [row["isbn"] for row in rows]
    books = Book.objects.filter(isbn__in=isbns, stockqty__gt=0)
    book_map = {book.isbn: book for book in books}

    ranked_books = []
    for row in rows:
        book = book_map.get(row["isbn"])
        if book:
            ranked_books.append(_rank_book_data(book, metric_label, row.get(metric_key, 0)))
    return ranked_books


def rankings(request: HttpRequest) -> HttpResponse:
    """商城榜单页：复用订单、库存和图书数据生成多个实用榜单。"""
    recent_cutoff = timezone.now() - timedelta(days=30)

    best_seller_rows = Orderdetail.objects.values("isbn").annotate(
        total_sales=Sum("quantity")
    ).order_by("-total_sales")[:20]

    recent_hot_rows = Orderdetail.objects.filter(
        orderid__orderdate__gte=recent_cutoff
    ).values("isbn").annotate(
        recent_sales=Sum("quantity")
    ).order_by("-recent_sales")[:20]

    low_stock = Book.objects.filter(stockqty__gt=0, stockqty__lte=F("minstocklimit")).order_by("stockqty", "title")[:10]

    rich_descriptions = Book.objects.filter(
        stockqty__gt=0
    ).exclude(description__isnull=True).exclude(description="").order_by("title")[:10]

    sections = [
        {
            "title": "畅销榜",
            "subtitle": "按历史订单销量排序，适合作为热门采购参考。",
            "icon": "local_fire_department",
            "books": _ranked_books_from_order_rows(best_seller_rows, "total_sales", "销量")[:10],
        },
        {
            "title": "近30天热销",
            "subtitle": "观察最近一段时间更受欢迎的图书。",
            "icon": "trending_up",
            "books": _ranked_books_from_order_rows(recent_hot_rows, "recent_sales", "近30天销量")[:10],
        },
        {
            "title": "库存紧俏",
            "subtitle": "库存低于预警线的图书，适合提醒补货或优先下单。",
            "icon": "inventory_2",
            "books": [_rank_book_data(book, "库存", book.stockqty) for book in low_stock],
        },
        {
            "title": "有简介可读",
            "subtitle": "优先展示已有简介的图书，方便用户做购买判断。",
            "icon": "menu_book",
            "books": [_rank_book_data(book, "库存", book.stockqty) for book in rich_descriptions],
        },
    ]

    return render(request, "bookstore/rankings.html", {"sections": sections})

def book_detail(request: HttpRequest, isbn: str) -> HttpResponse:
    book = get_object_or_404(Book, pk=isbn)

    # 记录用户浏览行为（仅对登录用户）
    if request.session.get("customer_id"):
        from .tracking import record_browse
        record_browse(request.session["customer_id"], isbn)

    book_data = {
        'isbn': book.isbn,
        'title': book.title,
        'publisher': book.publisher,
        'price': book.price,
        'keywords': book.keywords,
        'stockqty': book.stockqty,
        'location': book.location,
        'minstocklimit': book.minstocklimit,
        'description': book.description,
        'coverimage': None,
        'cover_image_url': None
    }

    # 优先使用数据库中的URL封面
    if book.coverimage:
        cover_url = book.coverimage
        if isinstance(cover_url, bytes):
            try:
                cover_url = cover_url.decode('utf-8')
            except:
                cover_url = None
        elif isinstance(cover_url, str):
            import re
            cover_url = re.sub(r"^b['\"]|['\"]$", "", cover_url)
            if cover_url.startswith("b'") or cover_url.startswith('b"'):
                cover_url = cover_url[2:-1]
        
        if cover_url and (cover_url.startswith('http://') or cover_url.startswith('https://')):
            book_data['cover_image_url'] = cover_url
    if not book_data['cover_image_url']:
        static_image = get_book_cover_image(book.title)
        if static_image:
            book_data['cover_image_url'] = static_image

    from django.conf import settings
    from urllib.parse import quote
    default_filename = getattr(settings, "DEFAULT_COVER_IMAGE_FILENAME", "Python编程从入门到实践.jpg")
    images_subdir = getattr(settings, "COVER_IMAGE_SUBDIR", "images")
    static_prefix = settings.STATIC_URL if settings.STATIC_URL.endswith('/') else settings.STATIC_URL + '/'
    default_cover_url = f"{static_prefix}{images_subdir}/{quote(default_filename)}"

    _ensure_book_favorite_table()
    customer_id = request.session.get("customer_id")
    is_favorited = False
    favorite_folder_id = None
    favorite_folders = []
    if customer_id:
        favorite = BookFavorite.objects.filter(customer_id=customer_id, isbn_id=isbn).first()
        is_favorited = favorite is not None
        favorite_folder_id = favorite.folder_id if favorite else None
        favorite_folders = _favorite_folders_for_customer(customer_id)
    favorite_count = BookFavorite.objects.filter(isbn_id=isbn).count()

    return render(request, "bookstore/book_detail.html", {
        "book": book_data,
        "DEFAULT_COVER_IMAGE_URL": default_cover_url,
        "is_favorited": is_favorited,
        "favorite_count": favorite_count,
        "favorite_folders": favorite_folders,
        "favorite_folder_id": favorite_folder_id,
    })

def search(request: HttpRequest) -> HttpResponse:
    query = request.GET.get("q", "").strip()
    recent_searches: list[str] = []
    books_with_covers: list = []

    if query:
        books = Book.objects.all().order_by("title")
        books = books.filter(
            Q(title__icontains=query) | Q(keywords__icontains=query) | Q(isbn__icontains=query)
        )
        if request.session.get("customer_id"):
            from .tracking import record_search
            record_search(request.session["customer_id"], query)
        books_with_covers = [_build_book_data(book) for book in books]
    else:
        customer_id = request.session.get("customer_id")
        if customer_id:
            from .tracking import get_recent_search_keywords
            recent_searches = get_recent_search_keywords(customer_id)

    from django.conf import settings
    from urllib.parse import quote
    default_filename = getattr(settings, "DEFAULT_COVER_IMAGE_FILENAME", "Python编程从入门到实践.jpg")
    images_subdir = getattr(settings, "COVER_IMAGE_SUBDIR", "images")
    static_prefix = settings.STATIC_URL if settings.STATIC_URL.endswith('/') else settings.STATIC_URL + '/'
    default_cover_url = f"{static_prefix}{images_subdir}/{quote(default_filename)}"
    
    return render(request, "bookstore/search.html", {
        "books": books_with_covers,
        "query": query,
        "recent_searches": recent_searches,
        "DEFAULT_COVER_IMAGE_URL": default_cover_url
    })

def _get_cart(request):
    """读取购物车（与 APP 共用 cache，按 customer_id 存储）。"""
    return get_cart(request.session["customer_id"])

def _save_cart(request, cart):
    save_cart(request.session["customer_id"], cart)


def _ensure_book_favorite_table():
    with connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `favorite_folder` (
                `ID` INT NOT NULL AUTO_INCREMENT,
                `customer_id` INT NOT NULL,
                `name` VARCHAR(60) NOT NULL,
                `is_default` TINYINT NOT NULL DEFAULT 0,
                `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                PRIMARY KEY (`ID`),
                UNIQUE KEY `favorite_folder_customer_name` (`customer_id`, `name`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `book_favorite` (
                `ID` INT NOT NULL AUTO_INCREMENT,
                `customer_id` INT NOT NULL,
                `isbn` VARCHAR(20) NOT NULL,
                `folder_id` INT NULL,
                `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                PRIMARY KEY (`ID`),
                UNIQUE KEY `book_favorite_customer_isbn` (`customer_id`, `isbn`),
                KEY `book_favorite_folder_idx` (`folder_id`),
                KEY `book_favorite_isbn_idx` (`isbn`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        cursor.execute("SHOW COLUMNS FROM `book_favorite` LIKE 'folder_id'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE `book_favorite` ADD COLUMN `folder_id` INT NULL AFTER `isbn`")
            cursor.execute("ALTER TABLE `book_favorite` ADD KEY `book_favorite_folder_idx` (`folder_id`)")


def _get_default_favorite_folder(customer_id: int) -> FavoriteFolder:
    _ensure_book_favorite_table()
    folder = FavoriteFolder.objects.filter(customer_id=customer_id, is_default=1).first()
    if folder:
        return folder
    return FavoriteFolder.objects.create(customer_id=customer_id, name="默认收藏夹", is_default=1)


def _favorite_folders_for_customer(customer_id: int):
    _get_default_favorite_folder(customer_id)
    return FavoriteFolder.objects.filter(customer_id=customer_id).order_by("-is_default", "created_at")


@require_POST
def favorite_toggle(request: HttpRequest, isbn: str) -> JsonResponse:
    customer_id = request.session.get("customer_id")
    if not customer_id:
        return JsonResponse({
            "success": False,
            "message": "请先登录后再收藏图书。",
            "login_url": reverse("bookstore:login"),
        }, status=401)

    get_object_or_404(Book, pk=isbn)
    _ensure_book_favorite_table()

    favorite = BookFavorite.objects.filter(customer_id=customer_id, isbn_id=isbn).first()
    if favorite:
        favorite.delete()
        is_favorited = False
        message = "已取消收藏"
        folder_id = None
    else:
        requested_folder_id = request.POST.get("folder_id")
        folder = None
        if requested_folder_id:
            folder = FavoriteFolder.objects.filter(id=requested_folder_id, customer_id=customer_id).first()
        if folder is None:
            folder = _get_default_favorite_folder(customer_id)

        BookFavorite.objects.create(customer_id=customer_id, isbn_id=isbn, folder=folder)
        is_favorited = True
        folder_id = folder.id
        message = f"已加入「{folder.name}」"

    favorite_count = BookFavorite.objects.filter(isbn_id=isbn).count()
    from .recommendations import invalidate_recommendation_cache
    invalidate_recommendation_cache(customer_id=customer_id)

    return JsonResponse({
        "success": True,
        "is_favorited": is_favorited,
        "favorite_count": favorite_count,
        "folder_id": folder_id,
        "message": message,
    })


@customer_required
@require_POST
def favorite_folder_create(request: HttpRequest) -> JsonResponse:
    customer_id = request.session["customer_id"]
    _ensure_book_favorite_table()
    name = request.POST.get("name", "").strip()
    if not name:
        return JsonResponse({"success": False, "message": "收藏夹名称不能为空"}, status=400)
    if len(name) > 60:
        return JsonResponse({"success": False, "message": "收藏夹名称不能超过60个字符"}, status=400)
    if FavoriteFolder.objects.filter(customer_id=customer_id, name=name).exists():
        return JsonResponse({"success": False, "message": "该收藏夹名称已存在"}, status=400)

    folder = FavoriteFolder.objects.create(customer_id=customer_id, name=name, is_default=0)
    return JsonResponse({
        "success": True,
        "message": f"收藏夹「{name}」创建成功",
        "folder": {"id": folder.id, "name": folder.name},
    })


@customer_required
def favorite_folders(request: HttpRequest) -> HttpResponse:
    customer_id = request.session["customer_id"]
    customer = get_object_or_404(Customer, pk=customer_id)
    _ensure_book_favorite_table()

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if not name:
            messages.error(request, "收藏夹名称不能为空")
        elif len(name) > 60:
            messages.error(request, "收藏夹名称不能超过60个字符")
        elif FavoriteFolder.objects.filter(customer_id=customer_id, name=name).exists():
            messages.error(request, "该收藏夹名称已存在")
        else:
            FavoriteFolder.objects.create(customer_id=customer_id, name=name, is_default=0)
            messages.success(request, f"收藏夹「{name}」创建成功")
        return redirect("bookstore:favorite_folders")

    folders = list(_favorite_folders_for_customer(customer_id))
    folder_ids = [folder.id for folder in folders]
    favorites = BookFavorite.objects.filter(
        customer_id=customer_id,
        folder_id__in=folder_ids,
    ).select_related("isbn", "folder").order_by("folder_id", "-created_at")

    favorite_map = {folder.id: [] for folder in folders}
    for favorite in favorites:
        favorite_map.setdefault(favorite.folder_id, []).append(_build_book_data(favorite.isbn))

    folder_cards = []
    total_count = 0
    for folder in folders:
        books = favorite_map.get(folder.id, [])
        total_count += len(books)
        folder_cards.append({
            "folder": folder,
            "books": books,
            "count": len(books),
        })

    return render(request, "bookstore/favorite_folders.html", {
        "customer": customer,
        "folder_cards": folder_cards,
        "total_count": total_count,
    })


@customer_required
@require_POST
def favorite_folder_delete(request: HttpRequest, folder_id: int) -> HttpResponse:
    customer_id = request.session["customer_id"]
    _ensure_book_favorite_table()
    folder = get_object_or_404(FavoriteFolder, pk=folder_id, customer_id=customer_id)

    if folder.is_default:
        messages.error(request, "默认收藏夹不能删除")
        return redirect("bookstore:favorite_folders")

    folder_name = folder.name
    with transaction.atomic():
        BookFavorite.objects.filter(customer_id=customer_id, folder=folder).delete()
        folder.delete()

    from .recommendations import invalidate_recommendation_cache
    invalidate_recommendation_cache(customer_id=customer_id)
    messages.success(request, f"收藏夹「{folder_name}」已删除")
    return redirect("bookstore:favorite_folders")

@customer_required
def cart_add(request: HttpRequest, isbn: str) -> HttpResponse:
    book = get_object_or_404(Book, pk=isbn)
    cart = _get_cart(request)
    
    # 支持POST方式传递数量
    if request.method == "POST":
        try:
            quantity = int(request.POST.get("quantity", 1))
            if quantity < 1:
                quantity = 1
        except (ValueError, TypeError):
            quantity = 1
    else:
        quantity = 1
    
    item = cart.get(isbn, {"quantity": 0})
    item["quantity"] += quantity
    cart[isbn] = item
    _save_cart(request, cart)
    
    messages.success(request, f"已将《{book.title}》× {quantity} 加入购物车")

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        cart_count = sum(item.get("quantity", 0) for item in cart.values())
        return JsonResponse({
            "success": True,
            "message": f"已将《{book.title}》× {quantity} 加入购物车",
            "cart_count": cart_count,
        })

    # 获取来源页面，返回原页面而不是跳转到购物车
    referer = request.META.get('HTTP_REFERER', '')
    if '/cart/' in referer or not referer:
        return redirect("bookstore:cart_detail")
    else:
        return redirect(referer)

@customer_required
def cart_update(request: HttpRequest, isbn: str) -> HttpResponse:
    """更新购物车中商品的数量"""
    if request.method == "POST":
        cart = _get_cart(request)
        try:
            quantity = int(request.POST.get("quantity", 0))
            if quantity > 0:
                cart[isbn] = {"quantity": quantity}
                messages.success(request, "购物车已更新")
            elif quantity == 0:
                # 数量为0则删除
                if isbn in cart:
                    del cart[isbn]
                messages.info(request, "已从购物车移除")
            _save_cart(request, cart)
        except (ValueError, TypeError):
            messages.error(request, "请输入有效的数量")
    return redirect("bookstore:cart_detail")


@customer_required
def cart_remove(request: HttpRequest, isbn: str) -> HttpResponse:
    cart = _get_cart(request)
    if isbn in cart:
        del cart[isbn]
        _save_cart(request, cart)
        messages.success(request, "已从购物车移除")
    return redirect("bookstore:cart_detail")

@customer_required
def cart_detail(request: HttpRequest) -> HttpResponse:
    cart = _get_cart(request)
    items = []
    original_total = Decimal('0')
    
    # 获取顾客的信用等级折扣率
    customer = get_object_or_404(Customer, pk=request.session["customer_id"])
    discount_rate = customer.levelid.discountrate
    discount_percent = (Decimal('1') - discount_rate) * 100  # 转换为百分比

    for isbn, data in cart.items():
        book = get_object_or_404(Book, pk=isbn)
        book_data = _build_book_data(book)
        setattr(book, "cover_image_url", book_data.get("cover_image_url"))
        cover_b64 = None
        if not book_data.get("cover_image_url") and getattr(book, "coverimage", None):
            try:
                import base64
                import re
                raw = book.coverimage
                if isinstance(raw, str):
                    s = raw.strip()
                    if re.fullmatch(r'[A-Za-z0-9+/=\s]+', s) and len(s) > 50:
                        cover_b64 = s.replace('\\n', '').replace('\\r', '')
                    else:
                        cover_b64 = base64.b64encode(s.encode('utf-8')).decode('utf-8')
                else:
                    cover_b64 = base64.b64encode(raw).decode('utf-8')
            except Exception:
                cover_b64 = None
        setattr(book, "coverimage_b64", cover_b64)
        quantity = data["quantity"]
        original_amount = book.price * quantity
        discounted_amount = original_amount * discount_rate
        original_total += original_amount
        items.append({
            "book": book,
            "quantity": quantity,
            "original_amount": original_amount,
            "discounted_amount": discounted_amount,
        })

    discounted_total = original_total * discount_rate
    discount_amount = original_total - discounted_total

    return render(request, "bookstore/cart.html", {
        "items": items,
        "original_total": original_total,
        "discounted_total": discounted_total,
        "discount_amount": discount_amount,
        "discount_rate": discount_rate,
        "discount_percent": discount_percent,
        "customer": customer,
        "DEFAULT_COVER_IMAGE_URL": _default_cover_url(),
    })

@customer_required
def order_confirm(request: HttpRequest) -> HttpResponse:
    cart = _get_cart(request)
    if not cart:
        messages.warning(request, "购物车为空")
        return redirect("bookstore:index")

    customer = get_object_or_404(Customer, pk=request.session["customer_id"])
    discount_rate = customer.levelid.discountrate
    discount_percent = (Decimal('1') - discount_rate) * 100

    if request.method == "POST":
        payment_choice = request.POST.get("payment_choice", "balance")

        # 获取发货地址信息
        shipping_name = request.POST.get("shipping_name", customer.name)
        shipping_contact = request.POST.get("shipping_contact", customer.email)
        shipping_address = request.POST.get("shipping_address", customer.address)

        # 验证发货地址
        if not shipping_address or not shipping_address.strip():
            messages.error(request, "请填写发货地址")
            return redirect("bookstore:order_confirm")

        with transaction.atomic():
            # 锁定客户记录
            customer = Customer.objects.select_for_update().select_related('levelid').get(pk=customer.customerid)

            # 1. 创建订单
            now = timezone.now()
            # 生成订单号：YYYYMMDDNN（年月日+两位序号）
            date_prefix = now.strftime('%Y%m%d')
            # 查找今天已有的订单数量
            today_orders_count = Orders.objects.filter(
                orderno__startswith=date_prefix
            ).count()
            order_number = f"{date_prefix}{today_orders_count + 1:02d}"

            # 组合发货地址信息
            full_shipping_address = f"{shipping_name} ({shipping_contact}) - {shipping_address}"

            order = Orders.objects.create(
                orderno=order_number,
                orderdate=now,
                customerid=customer,
                shipaddress=full_shipping_address,
                totalamount=Decimal('0'),
                actualpaid=Decimal('0'),
                paymentstatus=0,  # 默认未付款
                status=0,
            )

            # 2. 为购物车中每本书创建 Orderdetail（触发器会自动扣减库存）
            created_details = []
            for isbn, data in cart.items():
                book = get_object_or_404(Book, pk=isbn)
                quantity = data["quantity"]

                detail = Orderdetail.objects.create(
                    orderid=order,
                    isbn=book,
                    quantity=quantity,
                    unitprice=book.price,
                    isshipped=0,
                )
                created_details.append((book, quantity))

            # 3. 刷新订单获取触发器计算的总金额
            order.refresh_from_db()
            total_amount = order.totalamount or Decimal('0')
            
            print(f"🔍 [DEBUG] Order created: OrderID={order.orderid}, TotalAmount={total_amount}")
            
            if total_amount == 0:
                # TotalAmount为0说明触发器没有正确计算，可能是事务问题
                # 手动计算总金额
                from django.db.models import Sum
                manual_total = Orderdetail.objects.filter(orderid=order).aggregate(
                    total=Sum(F('quantity') * F('unitprice'))
                )['total'] or Decimal('0')
                # 应用折扣
                total_amount = manual_total * customer.levelid.discountrate
                order.totalamount = total_amount
                order.save(update_fields=['totalamount'])
                print(f"🔍 [DEBUG] Manual calculation: TotalAmount={total_amount}")
            
            # 4. 处理付款 (payment_choice已经在前面获取了)
            
            if payment_choice == "credit":
                # 纯信用支付
                from .signals import process_payment
                success, result = process_payment(order, customer, use_credit_only=True)
                
                if success:
                    msg, actual_paid, payment_status = result
                    order.actualpaid = actual_paid
                    order.paymentstatus = payment_status
                    order.save(update_fields=['actualpaid', 'paymentstatus'])
                    
                    # 清空购物车（Web / APP 共用 cache）
                    clear_cart(customer.customerid)
                    messages.success(request, f"下单成功！{msg}")
                    return redirect("bookstore:order_list")
                else:
                    # 失败，取消订单
                    order.status = 4
                    order.save(update_fields=['status'])
                    messages.error(request, f"下单失败：{result}。订单已取消。")
                    return redirect("bookstore:cart_detail")
            
            else:
                # 立即支付（余额优先）
                from .signals import process_payment
                success, result = process_payment(order, customer, use_credit_only=False)
                
                if success:
                    msg, actual_paid, payment_status = result
                    order.actualpaid = actual_paid
                    order.paymentstatus = payment_status
                    order.save(update_fields=['actualpaid', 'paymentstatus'])
                    
                    clear_cart(customer.customerid)
                    messages.success(request, f"下单成功！{msg}")
                    return redirect("bookstore:order_list")
                else:
                    # 失败，取消订单
                    order.status = 4
                    order.save(update_fields=['status'])
                    messages.error(request, f"下单失败：{result}。订单已取消。")
                    return redirect("bookstore:cart_detail")
            

    # GET 请求：先展示确认页（显示折扣信息）
    items = []
    original_total = Decimal('0')
    for isbn, data in cart.items():
        book = get_object_or_404(Book, pk=isbn)
        quantity = data["quantity"]
        original_amount = book.price * quantity
        discounted_amount = original_amount * discount_rate
        original_total += original_amount
        items.append({
            "book": book,
            "quantity": quantity,
            "original_amount": original_amount,
            "discounted_amount": discounted_amount,
        })

    discounted_total = original_total * discount_rate
    discount_amount = original_total - discounted_total

    return render(request, "bookstore/order_confirm.html", {
        "items": items,
        "original_total": original_total,
        "discounted_total": discounted_total,
        "discount_amount": discount_amount,
        "discount_rate": discount_rate,
        "discount_percent": discount_percent,
        "customer": customer,
    })

@customer_required
def order_list(request: HttpRequest) -> HttpResponse:
    customer = get_object_or_404(Customer, pk=request.session["customer_id"])
    orders = Orders.objects.filter(customerid=customer).order_by("-orderdate")
    
    # 为每个订单计算原始金额（用于显示折扣）
    orders_with_details = []
    for order in orders:
        details = Orderdetail.objects.filter(orderid=order)
        original_amount = sum(detail.quantity * detail.unitprice for detail in details)
        orders_with_details.append({
            "order": order,
            "original_amount": original_amount,
            "discount_amount": original_amount - (order.totalamount or 0),
        })
    
    return render(request, "bookstore/order_list.html", {
        "orders_with_details": orders_with_details,
        "customer": customer,
    })


@customer_required
def order_detail(request: HttpRequest, order_id: int) -> HttpResponse:
    customer = get_object_or_404(Customer, pk=request.session["customer_id"])
    order = get_object_or_404(Orders, pk=order_id, customerid=customer)
    details = Orderdetail.objects.filter(orderid=order)
    
    # 计算原始总金额和折扣信息
    original_amount = sum(detail.quantity * detail.unitprice for detail in details)
    discount_amount = original_amount - (order.totalamount or 0)
    discount_rate = customer.levelid.discountrate
    discount_percent = (Decimal('1') - discount_rate) * 100
    
    # 为每个明细计算折扣后金额
    details_with_discount = []
    for detail in details:
        original_item_amount = detail.quantity * detail.unitprice
        discounted_item_amount = original_item_amount * discount_rate
        details_with_discount.append({
            "detail": detail,
            "original_item_amount": original_item_amount,
            "discounted_item_amount": discounted_item_amount,
        })
    
    return render(
        request,
        "bookstore/order_detail.html",
        {
            "order": order,
            "details_with_discount": details_with_discount,
            "original_amount": original_amount,
            "discount_amount": discount_amount,
            "discount_rate": discount_rate,
            "discount_percent": discount_percent,
            "customer": customer,
        },
    )


@customer_required
def account_edit(request: HttpRequest) -> HttpResponse:
    """编辑账户信息"""
    customer = get_object_or_404(Customer, pk=request.session["customer_id"])

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        address = request.POST.get("address", "").strip()
        current_password = request.POST.get("current_password", "")
        new_password = request.POST.get("new_password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        # 验证输入
        if not name or not email:
            messages.error(request, "姓名和邮箱不能为空")
            return redirect("bookstore:account")

        # 检查邮箱是否已被其他用户使用
        if Customer.objects.filter(email=email).exclude(customerid=customer.customerid).exists():
            messages.error(request, "邮箱已被其他用户使用")
            return redirect("bookstore:account")

        # 如果要修改密码
        if new_password:
            if customer.password != current_password:
                messages.error(request, "当前密码不正确")
                return redirect("bookstore:account")

            if new_password != confirm_password:
                messages.error(request, "两次输入的新密码不一致")
                return redirect("bookstore:account")

            if len(new_password) < 6:
                messages.error(request, "新密码长度至少6位")
                return redirect("bookstore:account")

            customer.password = new_password

        # 更新基本信息
        customer.name = name
        customer.email = email
        customer.address = address
        customer.save()

        # 更新session中的姓名
        request.session["customer_name"] = name

        messages.success(request, "账户信息更新成功")
        return redirect("bookstore:account")

    return redirect("bookstore:account")


@customer_required
def account_recharge(request: HttpRequest) -> HttpResponse:
    """账户充值"""
    customer = get_object_or_404(Customer, pk=request.session["customer_id"])
    
    if request.method == "POST":
        try:
            amount = Decimal(request.POST.get("amount", "0"))
            if amount <= 0:
                messages.error(request, "充值金额必须大于0")
            else:
                with transaction.atomic():
                    customer = Customer.objects.select_for_update().get(pk=customer.customerid)
                    customer.balance += amount
                    # 充值不影响UsedCredit，只更新余额
                    customer.save(update_fields=['balance'])
                messages.success(request, f"充值成功！充值金额：¥{amount}，当前余额：¥{customer.balance}")
                return redirect("bookstore:account")
        except (ValueError, TypeError):
            messages.error(request, "请输入有效的金额")
        except Exception as e:
            messages.error(request, f"充值失败：{e}")
    
    # 计算折扣百分比
    discount_percent = (Decimal('1') - customer.levelid.discountrate) * 100
    
    # 计算距离下一级还需多少
    current_level = customer.levelid.levelid
    current_spent = customer.totalspent
    
    level_thresholds = {
        1: Decimal('1000'),    # 1级→2级需要1000
        2: Decimal('2000'),    # 2级→3级需要2000
        3: Decimal('5000'),    # 3级→4级需要5000
        4: Decimal('10000'),   # 4级→5级需要10000
        5: None,               # 5级是最高级
    }
    
    next_threshold = level_thresholds.get(current_level)
    if next_threshold:
        next_level_amount = next_threshold - current_spent
        if next_level_amount < 0:
            next_level_amount = Decimal('0')
    else:
        next_level_amount = None  # 已是最高级
    
    return render(request, "bookstore/account.html", {
        "customer": customer,
        "discount_percent": discount_percent,
        "next_level_amount": next_level_amount,
    })


@customer_required
def repay_overdraft(request: HttpRequest) -> HttpResponse:
    """全部还款 - 还清所有未全额支付的订单"""
    customer = get_object_or_404(Customer, pk=request.session["customer_id"])
    
    if request.method == "POST":
        with transaction.atomic():
            customer = Customer.objects.select_for_update().select_related('levelid').get(pk=customer.customerid)
            
            if customer.usedcredit <= 0:
                messages.info(request, "您当前没有未还款的订单")
                return redirect("bookstore:account")
            
            # 检查余额是否足够
            if customer.balance < customer.usedcredit:
                messages.error(request, f"余额不足！需要¥{customer.usedcredit}，当前余额¥{customer.balance}，请先充值")
                return redirect("bookstore:account")
            
            # 1. 获取所有未全额支付的订单
            unpaid_orders = Orders.objects.filter(
                customerid=customer,
                paymentstatus=2,  # 未全额支付
                status__in=[0, 1]  # 排除已取消和已完成
            )
            
            total_repay = Decimal('0')
            repay_count = 0
            
            # 2. 还款所有订单
            for order in unpaid_orders:
                unpaid_amount = order.totalamount - order.actualpaid
                
                # 从余额扣款
                customer.balance -= unpaid_amount
                customer.totalspent += unpaid_amount  # 还款计入累计消费
                total_repay += unpaid_amount
                
                # 更新订单
                order.actualpaid = order.totalamount
                order.paymentstatus = 1  # 已全额支付
                order.save(update_fields=['actualpaid', 'paymentstatus'])
                repay_count += 1
            
            # 3. 清空已使用信用额度
            customer.usedcredit = Decimal('0')
            
            # 4. 检查是否升级
            from .signals import _calculate_credit_level
            from .models import Creditlevel as CL
            new_level_id = _calculate_credit_level(customer.totalspent)
            old_level = customer.levelid.levelid
            if new_level_id != old_level:
                customer.levelid = CL.objects.get(levelid=new_level_id)
                customer.save(update_fields=['balance', 'usedcredit', 'totalspent', 'levelid'])
                messages.success(request, 
                    f"还款成功！还清了{repay_count}个订单，共¥{total_repay}，"
                    f"当前余额：¥{customer.balance}，"
                    f"信用等级已升级至{new_level_id}级！")
            else:
                customer.save(update_fields=['balance', 'usedcredit', 'totalspent'])
                messages.success(request, 
                    f"还款成功！还清了{repay_count}个订单，共¥{total_repay}，"
                    f"当前余额：¥{customer.balance}")
        
        return redirect("bookstore:account")
    
    return redirect("bookstore:account")


@customer_required
def pay_order(request: HttpRequest, order_id: int) -> HttpResponse:
    """补足支付未全额支付的订单（只能用余额）"""
    customer = get_object_or_404(Customer, pk=request.session["customer_id"])
    order = get_object_or_404(Orders, pk=order_id, customerid=customer)
    
    if order.paymentstatus == 1:
        messages.info(request, "该订单已全额支付")
        return redirect("bookstore:order_detail", order_id=order_id)
    
    if order.paymentstatus != 2:
        messages.error(request, "该订单不需要补足支付")
        return redirect("bookstore:order_detail", order_id=order_id)
    
    if request.method == "POST":
        with transaction.atomic():
            customer = Customer.objects.select_for_update().select_related('levelid').get(pk=customer.customerid)
            order.refresh_from_db()
            
            # 计算未付金额
            unpaid_amount = order.totalamount - order.actualpaid
            
            # 检查余额（只能用余额，不能用信用）
            if customer.balance < unpaid_amount:
                messages.error(request, f"余额不足！需要¥{unpaid_amount}，当前余额¥{customer.balance}，请先充值")
                return redirect("bookstore:order_detail", order_id=order_id)
            
            # 从余额扣款
            customer.balance -= unpaid_amount
            customer.totalspent += unpaid_amount  # 补足部分计入累计消费
            customer.usedcredit -= unpaid_amount  # 释放信用额度
            
            # 检查是否升级
            from .signals import _calculate_credit_level
            from .models import Creditlevel as CL
            new_level_id = _calculate_credit_level(customer.totalspent)
            old_level = customer.levelid.levelid
            if new_level_id != old_level:
                customer.levelid = CL.objects.get(levelid=new_level_id)
            
            customer.save(update_fields=['balance', 'usedcredit', 'totalspent', 'levelid'])
            
            # 更新订单
            order.actualpaid = order.totalamount
            order.paymentstatus = 1  # 已全额支付
            order.save(update_fields=['actualpaid', 'paymentstatus'])
            
            if new_level_id != old_level:
                messages.success(request, f"补足支付成功！支付¥{unpaid_amount}，当前余额¥{customer.balance}，信用等级已升级至{new_level_id}级！")
            else:
                messages.success(request, f"补足支付成功！支付¥{unpaid_amount}，当前余额¥{customer.balance}")
        
        return redirect("bookstore:order_detail", order_id=order_id)
    
    return redirect("bookstore:order_detail", order_id=order_id)


@customer_required
def cancel_order(request: HttpRequest, order_id: int) -> HttpResponse:
    """取消订单（只能取消未发货的订单）"""
    customer = get_object_or_404(Customer, pk=request.session["customer_id"])
    order = get_object_or_404(Orders, pk=order_id, customerid=customer)

    # 检查订单是否可以取消
    if order.status == 4:
        messages.info(request, "该订单已取消")
        return redirect("bookstore:order_detail", order_id=order_id)

    if order.status == 1:
        messages.error(request, "已发货的订单不能取消，请联系客服")
        return redirect("bookstore:order_detail", order_id=order_id)

    if order.status == 2:
        messages.error(request, "已完成的订单不能取消")
        return redirect("bookstore:order_detail", order_id=order_id)

    if request.method == "POST":
        with transaction.atomic():
            # 更新订单状态为已取消
            order.status = 4
            order.save(update_fields=['status'])

            messages.success(request, "订单已取消")
            return redirect("bookstore:order_detail", order_id=order_id)

    return redirect("bookstore:order_detail", order_id=order_id)


@customer_required
def confirm_receipt(request: HttpRequest, order_id: int) -> HttpResponse:
    """确认收货"""
    customer = get_object_or_404(Customer, pk=request.session["customer_id"])
    order = get_object_or_404(Orders, pk=order_id, customerid=customer)

    if order.status != 1:
        messages.error(request, "只有已发货的订单才能确认收货")
        return redirect("bookstore:order_detail", order_id=order_id)

    if request.method == "POST":
        order.status = 2  # 已完成
        order.save(update_fields=['status'])
        messages.success(request, "已确认收货，感谢您的购买！")
        return redirect("bookstore:order_detail", order_id=order_id)

    return redirect("bookstore:order_detail", order_id=order_id)


# ============================================================================
# AI 聊天助手
# ============================================================================

def ai_chat(request: HttpRequest) -> HttpResponse:
    """AI 对话页面。"""
    from .ai_service import is_ai_configured
    from .ai_chat_store import get_ai_history_for_request

    return render(
        request,
        "bookstore/ai_chat.html",
        {
            "chat_history": get_ai_history_for_request(request),
            "ai_configured": is_ai_configured(),
        },
    )


@require_http_methods(["POST"])
def ai_chat_api(request: HttpRequest) -> JsonResponse:
    """接收用户消息，调用 AI 并返回 JSON 回复。"""
    from .ai_chat_store import get_ai_history_for_request, save_ai_history_for_request

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "请求格式错误。"}, status=400)

    user_message = (payload.get("message") or "").strip()
    if not user_message:
        return JsonResponse({"error": "请输入消息。"}, status=400)

    history = get_ai_history_for_request(request)

    try:
        from .ai_service import chat_with_ai, AIServiceError

        reply = chat_with_ai(history, user_message)
    except AIServiceError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except Exception:
        return JsonResponse({"error": "服务器内部错误，请稍后再试。"}, status=500)

    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": reply})
    save_ai_history_for_request(request, history)

    return JsonResponse({"reply": reply})


@require_http_methods(["POST"])
def ai_chat_clear(request: HttpRequest) -> JsonResponse:
    """清空当前会话的历史记录。"""
    from .ai_chat_store import clear_ai_history_for_request

    clear_ai_history_for_request(request)
    return JsonResponse({"ok": True})
