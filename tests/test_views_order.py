"""订单模块 订单视图单元测试

覆盖视图：order_confirm、order_list、order_detail、cancel_order、confirm_receipt

测试方法分布：
- 等价类：各状态合法取值
- 边界值：订单号序号递增（第 1 / 第 2 单）
- 场景法：下单主成功路径
- 独立路径：cancel_order 路径 + confirm_receipt 路径
"""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from bookstore.cart_store import get_cart, save_cart, clear_cart


pytestmark = pytest.mark.django_db


def _get_customer_id(client_):
    """从已登录 client 的 session 中提取 customer_id。"""
    return client_.session["customer_id"]


def _seed_cart(client_, isbn, qty):
    """通过 cache 预填购物车数据。"""
    cid = _get_customer_id(client_)
    save_cart(cid, {isbn: {"quantity": qty}})


# =============================================================
# order_confirm
# =============================================================

class TestOrderConfirm:

    def test_empty_cart_get_redirects_index(self, logged_client):
        """TC-ORD-010 场景：空购物车 GET 确认页 → 重定向首页。"""
        url = reverse("bookstore:order_confirm")
        resp = logged_client.get(url)
        assert resp.status_code == 302
        assert reverse("bookstore:index") in resp["Location"]

    def test_get_with_cart_renders_confirm_page(self, logged_client, book):
        """GET 含购物车 → 200 渲染确认页，上下文含 items 和折扣信息。"""
        _seed_cart(logged_client, book.isbn, 2)
        url = reverse("bookstore:order_confirm")
        resp = logged_client.get(url)
        assert resp.status_code == 200
        assert len(resp.context["items"]) == 1
        assert resp.context["original_total"] == Decimal("80") * 2
        assert resp.context["discount_rate"] == Decimal("0.90")

    def test_post_empty_address_rejected(self, logged_client, book):
        """TC-ORD-011 异常：POST 地址为空 → 重定向 + error 提示，订单不生成。"""
        from bookstore.models import Orders

        _seed_cart(logged_client, book.isbn, 1)
        url = reverse("bookstore:order_confirm")
        resp = logged_client.post(url, {
            "payment_choice": "balance",
            "shipping_name": "Alice",
            "shipping_contact": "a@x.com",
            "shipping_address": "   ",  # 空白字符串
        })
        assert resp.status_code == 302
        assert Orders.objects.count() == 0

    def test_post_success_creates_order_balance_payment(self, logged_client, customer, book, mocker):
        """TC-ORD-012 独立路径：余额支付成功 → 订单创建、状态 1、购物车清空。"""
        from bookstore.models import Orders

        # mock process_payment 返回成功
        mocker.patch(
            "bookstore.signals.process_payment",
            return_value=(True, ("支付成功", Decimal("144"), 1)),
        )
        _seed_cart(logged_client, book.isbn, 2)

        url = reverse("bookstore:order_confirm")
        resp = logged_client.post(url, {
            "payment_choice": "balance",
            "shipping_name": customer.name,
            "shipping_contact": customer.email,
            "shipping_address": "武汉市洪山区华中科技大学",
        })
        assert resp.status_code == 302
        assert reverse("bookstore:order_list") in resp["Location"]

        # 仅创建 1 个订单
        assert Orders.objects.count() == 1
        order = Orders.objects.get()
        # 订单号格式：YYYYMMDD + 01
        expected_prefix = timezone.now().strftime("%Y%m%d")
        assert order.orderno.startswith(expected_prefix)
        assert order.orderno.endswith("01")
        assert order.paymentstatus == 1
        assert order.actualpaid == Decimal("144")
        # 购物车已清空
        cart = get_cart(_get_customer_id(logged_client))
        assert cart == {}

    def test_post_orderno_increments_on_second_order(self, logged_client, customer, book, mocker):
        """TC-ORD-013 边界：同一天第 2 单，序号应为 02。"""
        from bookstore.models import Orders

        # 预置同日一条订单，订单号 01
        date_prefix = timezone.now().strftime("%Y%m%d")
        Orders.objects.create(
            orderno=f"{date_prefix}01",
            orderdate=timezone.now(),
            customerid=customer,
            shipaddress="x",
            totalamount=Decimal("50"),
            status=0,
        )

        mocker.patch(
            "bookstore.signals.process_payment",
            return_value=(True, ("OK", Decimal("72"), 1)),
        )
        _seed_cart(logged_client, book.isbn, 1)

        url = reverse("bookstore:order_confirm")
        logged_client.post(url, {
            "payment_choice": "balance",
            "shipping_name": customer.name,
            "shipping_contact": customer.email,
            "shipping_address": "武汉",
        })
        assert Orders.objects.count() == 2
        latest = Orders.objects.exclude(orderno=f"{date_prefix}01").get()
        assert latest.orderno == f"{date_prefix}02"


# =============================================================
# order_list
# =============================================================

class TestOrderList:

    def test_list_returns_only_current_user_orders(self, logged_client, customer, other_customer, book):
        """TC-ORD-020 等价类：只返回当前用户的订单。"""
        from bookstore.models import Orders

        # 当前用户 2 单
        for i in range(2):
            Orders.objects.create(
                orderno=f"ME00{i}",
                orderdate=timezone.now() - timedelta(days=i),
                customerid=customer,
                shipaddress="addr",
                totalamount=Decimal("50"),
                status=0,
            )
        # 他人 1 单
        Orders.objects.create(
            orderno="OTHER01",
            orderdate=timezone.now(),
            customerid=other_customer,
            shipaddress="addr",
            totalamount=Decimal("99"),
            status=0,
        )

        url = reverse("bookstore:order_list")
        resp = logged_client.get(url)
        assert resp.status_code == 200
        orders_ctx = resp.context["orders_with_details"]
        assert len(orders_ctx) == 2
        ordernos = [o["order"].orderno for o in orders_ctx]
        assert "OTHER01" not in ordernos

    def test_list_ordered_by_orderdate_desc(self, logged_client, customer):
        """场景：按订单日期倒序展示。"""
        from bookstore.models import Orders

        now = timezone.now()
        Orders.objects.create(
            orderno="OLD001", orderdate=now - timedelta(days=3),
            customerid=customer, shipaddress="x", totalamount=Decimal("10"), status=0,
        )
        Orders.objects.create(
            orderno="NEW001", orderdate=now,
            customerid=customer, shipaddress="x", totalamount=Decimal("10"), status=0,
        )
        url = reverse("bookstore:order_list")
        resp = logged_client.get(url)
        ordernos = [o["order"].orderno for o in resp.context["orders_with_details"]]
        assert ordernos == ["NEW001", "OLD001"]

    def test_list_empty(self, logged_client):
        """TC-ORD-021 边界：无订单时返回空列表。"""
        url = reverse("bookstore:order_list")
        resp = logged_client.get(url)
        assert resp.status_code == 200
        assert resp.context["orders_with_details"] == []


# =============================================================
# order_detail
# =============================================================

class TestOrderDetail:

    def test_own_order_returns_200(self, logged_client, order):
        """TC-ORD-030 等价类：访问自己的订单 → 200 + 明细。"""
        url = reverse("bookstore:order_detail", args=[order.orderid])
        resp = logged_client.get(url)
        assert resp.status_code == 200
        assert resp.context["order"].orderid == order.orderid
        assert len(resp.context["details_with_discount"]) == 1

    def test_other_user_order_returns_404(self, logged_client, other_customer, book):
        """TC-ORD-031 异常：访问别人的订单 → 404。"""
        from bookstore.models import Orders

        other_order = Orders.objects.create(
            orderno="OTHER_SEC",
            orderdate=timezone.now(),
            customerid=other_customer,
            shipaddress="addr",
            totalamount=Decimal("50"),
            status=0,
        )
        url = reverse("bookstore:order_detail", args=[other_order.orderid])
        resp = logged_client.get(url)
        assert resp.status_code == 404

    def test_nonexistent_order_returns_404(self, logged_client):
        """异常：不存在的 order_id → 404。"""
        url = reverse("bookstore:order_detail", args=[9999999])
        resp = logged_client.get(url)
        assert resp.status_code == 404

    def test_discount_fields_in_context(self, logged_client, order, book):
        """场景：订单详情返回折扣金额信息。"""
        url = reverse("bookstore:order_detail", args=[order.orderid])
        resp = logged_client.get(url)
        ctx = resp.context
        assert ctx["discount_rate"] == Decimal("0.90")
        # 原价 = 单价 * 数量
        assert ctx["original_amount"] == Decimal("80.00") * 1


# =============================================================
# cancel_order  （4 条独立路径）
# =============================================================

class TestCancelOrder:

    def _make_order(self, customer, status, book=None, orderno="CAN001"):
        from bookstore.models import Orders, Orderdetail
        o = Orders.objects.create(
            orderno=orderno,
            orderdate=timezone.now(),
            customerid=customer,
            shipaddress="addr",
            totalamount=Decimal("80"),
            actualpaid=Decimal("80"),
            paymentstatus=1,
            status=status,
        )
        if book:
            Orderdetail.objects.create(
                orderid=o, isbn=book, quantity=1, unitprice=book.price, isshipped=0
            )
        return o

    def test_cancel_pending_order_success(self, logged_client, customer, book):
        """TC-ORD-040 独立路径 Path-5：status=0 + POST → 成功取消。"""
        from bookstore.models import Orders

        o = self._make_order(customer, status=0, book=book)
        url = reverse("bookstore:cancel_order", args=[o.orderid])
        resp = logged_client.post(url)
        assert resp.status_code == 302
        assert Orders.objects.get(pk=o.orderid).status == 4

    def test_cancel_shipped_order_rejected(self, logged_client, customer, book):
        """TC-ORD-041 独立路径 Path-2：已发货订单（status=1）不可取消。"""
        from bookstore.models import Orders

        o = self._make_order(customer, status=1, book=book, orderno="CAN_SHIP")
        url = reverse("bookstore:cancel_order", args=[o.orderid])
        resp = logged_client.post(url)
        assert resp.status_code == 302
        assert Orders.objects.get(pk=o.orderid).status == 1

    def test_cancel_completed_order_rejected(self, logged_client, customer, book):
        """TC-ORD-042 独立路径 Path-3：已完成订单（status=2）不可取消。"""
        from bookstore.models import Orders

        o = self._make_order(customer, status=2, book=book, orderno="CAN_DONE")
        url = reverse("bookstore:cancel_order", args=[o.orderid])
        resp = logged_client.post(url)
        assert resp.status_code == 302
        assert Orders.objects.get(pk=o.orderid).status == 2

    def test_cancel_already_cancelled_is_idempotent(self, logged_client, customer, book):
        """TC-ORD-043 独立路径 Path-1：已取消订单（status=4）幂等提示。"""
        from bookstore.models import Orders

        o = self._make_order(customer, status=4, book=book, orderno="CAN_GONE")
        url = reverse("bookstore:cancel_order", args=[o.orderid])
        resp = logged_client.post(url)
        assert resp.status_code == 302
        assert Orders.objects.get(pk=o.orderid).status == 4

    def test_cancel_get_does_not_modify(self, logged_client, customer, book):
        """独立路径 Path-4：GET 请求，仅重定向到详情页，不改状态。"""
        from bookstore.models import Orders

        o = self._make_order(customer, status=0, book=book, orderno="CAN_GET")
        url = reverse("bookstore:cancel_order", args=[o.orderid])
        resp = logged_client.get(url)
        assert resp.status_code == 302
        assert Orders.objects.get(pk=o.orderid).status == 0


# =============================================================
# confirm_receipt
# =============================================================

class TestConfirmReceipt:

    def _make_order(self, customer, status, orderno):
        from bookstore.models import Orders
        return Orders.objects.create(
            orderno=orderno,
            orderdate=timezone.now(),
            customerid=customer,
            shipaddress="addr",
            totalamount=Decimal("80"),
            actualpaid=Decimal("80"),
            paymentstatus=1,
            status=status,
        )

    def test_confirm_shipped_order_success(self, logged_client, customer):
        """TC-ORD-050 独立路径：status=1 + POST → 改为 2。"""
        from bookstore.models import Orders

        o = self._make_order(customer, status=1, orderno="CFM001")
        url = reverse("bookstore:confirm_receipt", args=[o.orderid])
        resp = logged_client.post(url)
        assert resp.status_code == 302
        assert Orders.objects.get(pk=o.orderid).status == 2

    def test_confirm_pending_order_rejected(self, logged_client, customer):
        """TC-ORD-051 独立路径：status=0（未发货）不可确认收货。"""
        from bookstore.models import Orders

        o = self._make_order(customer, status=0, orderno="CFM_PEND")
        url = reverse("bookstore:confirm_receipt", args=[o.orderid])
        resp = logged_client.post(url)
        assert resp.status_code == 302
        assert Orders.objects.get(pk=o.orderid).status == 0

    def test_confirm_get_does_nothing(self, logged_client, customer):
        """GET 方法：仅重定向，不改状态。"""
        from bookstore.models import Orders

        o = self._make_order(customer, status=1, orderno="CFM_GET")
        url = reverse("bookstore:confirm_receipt", args=[o.orderid])
        resp = logged_client.get(url)
        assert resp.status_code == 302
        assert Orders.objects.get(pk=o.orderid).status == 1

    def test_confirm_others_order_404(self, logged_client, other_customer):
        """越权：确认别人的订单 → 404。"""
        o = self._make_order(other_customer, status=1, orderno="CFM_OTHER")
        url = reverse("bookstore:confirm_receipt", args=[o.orderid])
        resp = logged_client.post(url)
        assert resp.status_code == 404
