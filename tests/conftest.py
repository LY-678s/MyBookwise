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


# -------- 核心业务 fixture --------

@pytest.fixture
def creditlevels(db):
    """创建 5 个信用等级（与真实业务一致）。"""
    from bookstore.models import Creditlevel

    data = [
        (1, Decimal("0.90"), 0, Decimal("0")),      # 10% 折扣，不可透支
        (2, Decimal("0.85"), 0, Decimal("0")),      # 15% 折扣，不可透支
        (3, Decimal("0.85"), 1, Decimal("500")),    # 15% 折扣，可透支 500
        (4, Decimal("0.80"), 1, Decimal("2000")),   # 20% 折扣，可透支 2000
        (5, Decimal("0.75"), 1, Decimal("999999")), # 25% 折扣，无额度限制
    ]
    levels = {}
    for lid, rate, can, limit in data:
        obj, _ = Creditlevel.objects.get_or_create(
            levelid=lid,
            defaults={"discountrate": rate, "canusecredit": can, "creditlimit": limit},
        )
        levels[lid] = obj
    return levels


@pytest.fixture
def customer(db, creditlevels):
    """默认 1 级客户，余额 1000，无欠款。"""
    from django.utils import timezone
    from bookstore.models import Customer

    return Customer.objects.create(
        username="alice",
        password="123456",
        name="Alice",
        address="武汉市洪山区",
        email="alice@example.com",
        balance=Decimal("1000.00"),
        levelid=creditlevels[1],
        creditlimit=Decimal("0"),
        usedcredit=Decimal("0"),
        totalspent=Decimal("0"),
        registerdate=timezone.now(),
    )


@pytest.fixture
def customer_l3(db, creditlevels):
    """3 级客户，可透支 500。"""
    from django.utils import timezone
    from bookstore.models import Customer

    return Customer.objects.create(
        username="bob",
        password="123456",
        name="Bob",
        address="武汉市东湖",
        email="bob@example.com",
        balance=Decimal("300.00"),
        levelid=creditlevels[3],
        creditlimit=Decimal("500"),
        usedcredit=Decimal("0"),
        totalspent=Decimal("2500"),
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
