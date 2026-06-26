"""
pytest 全局 fixture 与环境 hook。
1. 项目 models.py 里所有模型都是 managed=False（Django 不建表），在测试库里需临时置为 True，
   再配合 settings_test 中 MIGRATION_MODULES 置 None 与 --run-syncdb，让 Django 自动建表。
2. 提供订单模块测试常用 fixture：信用等级、客户、图书、已登录 client、订单等。
"""
from __future__ import annotations

from decimal import Decimal

import django
import pytest


def pytest_configure(config):
    """在 pytest 收集测试之前，把 bookstore 的所有模型标记为 managed=True。"""
    django.setup()
    from django.apps import apps

    for model in apps.get_models():
        if model._meta.app_label == "bookstore":
            model._meta.managed = True


@pytest.fixture(scope="session")
def django_db_setup(django_db_blocker):
    """覆盖 pytest-django 默认的 django_db_setup：
    由于 MIGRATION_MODULES 里全部置 None 且 bookstore 没有迁移文件，
    需要显式调用 migrate --run-syncdb 让 Django 直接从模型定义建表。
    """
    from django.core.management import call_command

    with django_db_blocker.unblock():
        call_command("migrate", "--run-syncdb", verbosity=0, interactive=False)
    yield


@pytest.fixture(autouse=True)
def _clear_cache_each_test():
    """每个测试前清空 Django 缓存（购物车、AI 历史等），避免测试间数据累积。"""
    from django.core.cache import cache
    cache.clear()
    yield
    cache.clear()


# -------- 核心业务 fixture --------

@pytest.fixture(autouse=True)
def _clear_cart_items_each_test(db):
    """购物车已持久化到数据库，每个测试前后清理 cart_item。"""
    from bookstore.models import CartItem

    CartItem.objects.all().delete()
    yield
    CartItem.objects.all().delete()


@pytest.fixture
def creditlevels(db):
    """创建 0-5 级会员等级（积分制，无信用额度）。"""
    from bookstore.models import Creditlevel

    data = [
        (0, Decimal("1.00")),   # 非会员
        (1, Decimal("0.95")),
        (2, Decimal("0.93")),
        (3, Decimal("0.90")),
        (4, Decimal("0.88")),
        (5, Decimal("0.85")),
    ]
    levels = {}
    for lid, rate in data:
        obj, _ = Creditlevel.objects.get_or_create(
            levelid=lid,
            defaults={"discountrate": rate},
        )
        levels[lid] = obj
    return levels


@pytest.fixture
def customer(db, creditlevels):
    """默认 1 级客户。"""
    from django.utils import timezone
    from bookstore.models import Customer

    return Customer.objects.create(
        username="alice",
        password="123456",
        name="Alice",
        address="武汉市洪山区",
        email="alice@example.com",
        levelid=creditlevels[1],
        registerdate=timezone.now(),
    )


@pytest.fixture
def customer_l3(db, creditlevels):
    """3 级客户。"""
    from django.utils import timezone
    from bookstore.models import Customer

    return Customer.objects.create(
        username="bob",
        password="123456",
        name="Bob",
        address="武汉市东湖",
        email="bob@example.com",
        levelid=creditlevels[3],
        registerdate=timezone.now(),
    )


@pytest.fixture
def other_customer(db, creditlevels):
    """另一位客户，用于越权测试。"""
    from django.utils import timezone
    from bookstore.models import Customer

    return Customer.objects.create(
        username="mallory",
        password="123456",
        name="Mallory",
        address="未知",
        email="m@example.com",
        balance=Decimal("500"),
        levelid=creditlevels[1],
        creditlimit=Decimal("0"),
        usedcredit=Decimal("0"),
        totalspent=Decimal("0"),
        registerdate=timezone.now(),
    )


@pytest.fixture
def book(db):
    from bookstore.models import Book

    return Book.objects.create(
        isbn="9787111000001",
        title="Python 编程从入门到实践",
        publisher="机械工业出版社",
        price=Decimal("80.00"),
        keywords="python,编程",
        stockqty=100,
        minstocklimit=10,
    )


@pytest.fixture
def book2(db):
    from bookstore.models import Book

    return Book.objects.create(
        isbn="9787111000002",
        title="数据库系统概念",
        publisher="机械工业出版社",
        price=Decimal("120.00"),
        keywords="数据库",
        stockqty=50,
        minstocklimit=5,
    )


@pytest.fixture
def logged_client(client, customer):
    """已登录为 customer 的测试客户端。"""
    session = client.session
    session["customer_id"] = customer.customerid
    session["customer_name"] = customer.name
    session.save()
    return client


@pytest.fixture
def logged_client_l3(client, customer_l3):
    session = client.session
    session["customer_id"] = customer_l3.customerid
    session["customer_name"] = customer_l3.name
    session.save()
    return client


@pytest.fixture
def order(db, customer, book):
    """已有一个订单（status=0 未发货，paymentstatus=1 已付款）含 1 条明细。"""
    from django.utils import timezone
    from bookstore.models import Orders, Orderdetail

    o = Orders.objects.create(
        orderno="2099010101",
        orderdate=timezone.now(),
        customerid=customer,
        shipaddress="Alice (a@x.com) - 武汉市洪山区",
        totalamount=Decimal("80.00"),
        actualpaid=Decimal("80.00"),
        paymentstatus=1,
        status=0,
    )
    Orderdetail.objects.create(
        orderid=o,
        isbn=book,
        quantity=1,
        unitprice=book.price,
        isshipped=0,
    )
    return o


# -------- 성원 A/C 공통 fixture (bookstore/tests/conftest.py 에서 통합) --------

@pytest.fixture
def mock_customer_data():
    """모의 고객 데이터 (성원 A 용)"""
    return {
        'customerid': 1,
        'username': 'testuser',
        'password': 'testpass123',
        'name': '测试用户',
        'address': '测试地址',
        'email': 'test@example.com',
        'balance': Decimal('1000.00'),
        'creditlimit': Decimal('5000.00'),
        'usedcredit': Decimal('0.00'),
        'totalspent': Decimal('500.00'),
    }


@pytest.fixture
def mock_order_data():
    """모의 주문 데이터"""
    return {
        'orderid': 1,
        'orderno': 'ORD-20250101-0001',
        'totalamount': Decimal('200.00'),
        'actualpaid': Decimal('0.00'),
        'paymentstatus': 0,
        'status': 0,
    }


@pytest.fixture
def mock_creditlevel_data():
    """모의 신용 등급 데이터 (성원 C 용)"""
    return {
        1: {'discountrate': Decimal('1.00'), 'canusecredit': 0, 'creditlimit': Decimal('0.00')},
        2: {'discountrate': Decimal('0.98'), 'canusecredit': 1, 'creditlimit': Decimal('1000.00')},
        3: {'discountrate': Decimal('0.95'), 'canusecredit': 1, 'creditlimit': Decimal('3000.00')},
        4: {'discountrate': Decimal('0.90'), 'canusecredit': 1, 'creditlimit': Decimal('5000.00')},
        5: {'discountrate': Decimal('0.85'), 'canusecredit': 1, 'creditlimit': Decimal('10000.00')},
    }


@pytest.fixture
def payment_amounts():
    """결제 테스트 경계값 금액 (성원 C 용)"""
    return {
        'zero': Decimal('0.00'),
        'min_positive': Decimal('0.01'),
        'boundary_small': Decimal('99.99'),
        'boundary_medium': Decimal('100.00'),
        'boundary_large': Decimal('999.99'),
        'boundary_xl': Decimal('1000.00'),
        'max': Decimal('10000.00'),
    }


@pytest.fixture
def balance_amounts():
    """잔액 테스트 경계값 (성원 C 용)"""
    return {
        'zero': Decimal('0.00'),
        'min_positive': Decimal('0.01'),
        'exactly_equal': Decimal('100.00'),
        'just_over': Decimal('100.01'),
        'much_less': Decimal('50.00'),
        'much_more': Decimal('5000.00'),
    }
