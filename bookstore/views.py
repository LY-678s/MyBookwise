from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, F, Sum
from django.db import transaction

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
        payment_method = request.POST.get("payment_method", "immediate")  # immediate或defer
        
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
            
            order = Orders.objects.create(
                orderno=order_number,
                orderdate=now,
                customerid=customer,
                shipaddress=customer.address or "默认地址",
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
            
            # 4. 处理付款
            payment_choice = request.POST.get("payment_choice", "balance")  # balance或credit
            
            if payment_choice == "credit":
                # 纯信用支付
                from .signals import process_payment
                success, result = process_payment(order, customer, use_credit_only=True)
                
                if success:
                    msg, actual_paid, payment_status = result
                    order.actualpaid = actual_paid
                    order.paymentstatus = payment_status
                    order.save(update_fields=['actualpaid', 'paymentstatus'])
                    
                    # 清空购物车
                    request.session["cart"] = {}
                    request.session.modified = True
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
                    
                    # 清空购物车
                    request.session["cart"] = {}
                    request.session.modified = True
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