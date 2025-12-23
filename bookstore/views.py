from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q

from .models import Book, Customer, Orders, Orderdetail, Creditlevel
from decimal import Decimal
from functools import wraps


def customer_login(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        try:
            customer = Customer.objects.get(username=username, password=password)
            # 用 session 记录登录顾客的 ID
            request.session["customer_id"] = customer.customerid
            request.session["customer_name"] = customer.name
            messages.success(request, "登录成功")
            return redirect("bookstore:index")
        except Customer.DoesNotExist:
            messages.error(request, "用户名或密码错误")

    return render(request, "bookstore/login.html")
    

def customer_logout(request: HttpRequest) -> HttpResponse:
    request.session.pop("customer_id", None)
    request.session.pop("customer_name", None)
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


def index(request: HttpRequest) -> HttpResponse:
    books = Book.objects.all().order_by("title")
    return render(request, "bookstore/index.html", {"books": books})

def book_detail(request: HttpRequest, isbn: str) -> HttpResponse:
    book = get_object_or_404(Book, pk=isbn)
    return render(request, "bookstore/book_detail.html", {"book": book})

def search(request: HttpRequest) -> HttpResponse:
    query = request.GET.get("q", "")
    books = Book.objects.all()
    if query:
        books = books.filter(
            Q(title__icontains=query) | Q(keywords__icontains=query) | Q(isbn__icontains=query)
        )
    return render(request, "bookstore/search.html", {"books": books, "query": query})

def _get_cart(request):
    return request.session.setdefault("cart", {})

def _save_cart(request, cart):
    request.session["cart"] = cart
    request.session.modified = True

@customer_required
def cart_add(request: HttpRequest, isbn: str) -> HttpResponse:
    book = get_object_or_404(Book, pk=isbn)
    cart = _get_cart(request)
    item = cart.get(isbn, {"quantity": 0})
    item["quantity"] += 1
    cart[isbn] = item
    _save_cart(request, cart)
    messages.success(request, f"已将《{book.title}》加入购物车")
    return redirect("bookstore:cart_detail")

@customer_required
def cart_remove(request: HttpRequest, isbn: str) -> HttpResponse:
    cart = _get_cart(request)
    if isbn in cart:
        del cart[isbn]
        _save_cart(request, cart)
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
        # 1. 创建订单（totalamount设为0，让触发器自动计算折扣后的金额）
        now = timezone.now()
        order = Orders.objects.create(
            orderno=f"OD{int(now.timestamp())}{customer.customerid}",
            orderdate=now,
            customerid=customer,
            shipaddress=customer.address or "默认地址",
            totalamount=0,  # 设为0，触发器会在订单明细插入后自动计算折扣后的金额
            status=0,  # 0=已下单
        )

        # 2. 为购物车中每本书创建 Orderdetail
        for isbn, data in cart.items():
            book = get_object_or_404(Book, pk=isbn)
            quantity = data["quantity"]

            Orderdetail.objects.create(
                orderid=order,
                isbn=book,
                quantity=quantity,
                unitprice=book.price,
                isshipped=0,
            )

            # 3. 简单库存扣减（注意：这是直接操作，不考虑并发）
            book.stockqty -= quantity
            book.save()

        # 4. 触发器会自动计算订单总金额（应用折扣）并扣减余额
        # 刷新订单对象以获取触发器计算后的总金额
        order.refresh_from_db()

        # 5. 清空购物车
        request.session["cart"] = {}
        messages.success(request, f"下单成功，订单号：{order.orderno}，订单金额：¥{order.totalamount}")
        return redirect("bookstore:order_list")

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