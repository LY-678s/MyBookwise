"""订单模块 模型层单元测试

覆盖：
- Orders 模型：创建、字段校验、orderno 唯一约束、与 Customer 外键、状态字段默认值
- Orderdetail 模型：创建、与 Orders/Book 外键、数量字段
"""
from __future__ import annotations

from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone


pytestmark = pytest.mark.django_db


# --------------------- Orders 模型 ---------------------

class TestOrdersModel:
    """Orders 模型等价类/边界/异常测试。"""

    def test_create_orders_success(self, customer):
        """TC-ORD-001 等价类：正常创建一个订单，字段可回读。"""
        from bookstore.models import Orders

        order = Orders.objects.create(
            orderno="2025010101",
            orderdate=timezone.now(),
            customerid=customer,
            shipaddress="武汉市",
            totalamount=Decimal("100.00"),
            actualpaid=Decimal("100.00"),
            paymentstatus=1,
            status=0,
        )
        assert order.orderid is not None
        assert order.orderno == "2025010101"
        assert order.customerid.customerid == customer.customerid
        assert order.status == 0
        assert order.paymentstatus == 1

    def test_orderno_unique_constraint(self, customer):
        """TC-ORD-002 异常：orderno 唯一约束重复创建应抛 IntegrityError。"""
        from bookstore.models import Orders

        Orders.objects.create(
            orderno="DUP001",
            orderdate=timezone.now(),
            customerid=customer,
            shipaddress="addr",
            totalamount=Decimal("10"),
            status=0,
        )
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Orders.objects.create(
                    orderno="DUP001",
                    orderdate=timezone.now(),
                    customerid=customer,
                    shipaddress="addr2",
                    totalamount=Decimal("20"),
                    status=0,
                )

    def test_default_values(self, customer):
        """边界：未指定 actualpaid/paymentstatus，使用模型默认值。"""
        from bookstore.models import Orders

        order = Orders.objects.create(
            orderno="DEFAULT01",
            orderdate=timezone.now(),
            customerid=customer,
            shipaddress="addr",
            status=0,
        )
        assert order.actualpaid == Decimal("0")
        assert order.paymentstatus == 0

    def test_str_returns_orderno(self, customer):
        """Orders.__str__ 应返回订单号。"""
        from bookstore.models import Orders

        order = Orders.objects.create(
            orderno="STR001",
            orderdate=timezone.now(),
            customerid=customer,
            shipaddress="addr",
            status=0,
        )
        assert str(order) == "STR001"

    def test_foreign_key_customer(self, customer):
        """订单的 customerid 外键反查应能访问客户属性。"""
        from bookstore.models import Orders

        order = Orders.objects.create(
            orderno="FK001",
            orderdate=timezone.now(),
            customerid=customer,
            shipaddress="addr",
            status=0,
        )
        refetched = Orders.objects.get(pk=order.pk)
        assert refetched.customerid.username == "alice"

    @pytest.mark.parametrize("status_value", [0, 1, 2, 4])
    def test_status_values(self, customer, status_value):
        """等价类：status 各合法取值（0=未发货, 1=已发货, 2=已完成, 4=已取消）。"""
        from bookstore.models import Orders

        order = Orders.objects.create(
            orderno=f"ST{status_value}",
            orderdate=timezone.now(),
            customerid=customer,
            shipaddress="addr",
            status=status_value,
        )
        assert Orders.objects.get(pk=order.pk).status == status_value


# --------------------- Orderdetail 模型 ---------------------

class TestOrderdetailModel:

    def test_create_orderdetail_success(self, order, book):
        """TC-ORD-003 等价类：正常创建明细。"""
        from bookstore.models import Orderdetail

        detail = Orderdetail.objects.create(
            orderid=order,
            isbn=book,
            quantity=3,
            unitprice=book.price,
            isshipped=0,
        )
        assert detail.detailid is not None
        assert detail.quantity == 3
        assert detail.unitprice == book.price
        assert detail.orderid.orderid == order.orderid
        assert detail.isbn.isbn == book.isbn

    def test_orderdetail_str(self, order, book):
        """Orderdetail.__str__ 格式：orderno - 书名 x数量。"""
        from bookstore.models import Orderdetail

        detail = Orderdetail.objects.create(
            orderid=order,
            isbn=book,
            quantity=2,
            unitprice=book.price,
            isshipped=0,
        )
        s = str(detail)
        assert order.orderno in s
        assert book.title in s
        assert "x2" in s

    def test_orderdetail_reverse_relation(self, order, book):
        """一对多：Orders → Orderdetail 反向查询。"""
        from bookstore.models import Orderdetail

        Orderdetail.objects.create(
            orderid=order, isbn=book, quantity=1, unitprice=book.price, isshipped=0
        )
        count = Orderdetail.objects.filter(orderid=order).count()
        # order fixture 本身已有 1 条明细，加上这条共 2 条
        assert count == 2

    def test_orderdetail_quantity_boundary(self, order, book):
        """边界：quantity 最小值 1（业务上限暂无字段约束，只测底部）。"""
        from bookstore.models import Orderdetail

        detail = Orderdetail.objects.create(
            orderid=order,
            isbn=book,
            quantity=1,
            unitprice=book.price,
            isshipped=0,
        )
        assert detail.quantity == 1
