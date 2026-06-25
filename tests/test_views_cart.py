"""订单模块 购物车视图单元测试

覆盖视图：cart_add、cart_update、cart_remove、cart_detail

测试方法分布：
- 等价类：有效数量、不存在 ISBN、未登录
- 边界值：quantity = 0 / -1 / 空字符串
- 场景法：首次加入 / 重复加入累加 / 折扣计算
- 独立路径：cart_update 的 3 条分支（>0 / =0 / 异常）

注：购物车已从 session 迁移到 cache（cart_store.py），
    测试通过 get_cart / save_cart 操作缓存数据。
"""
from __future__ import annotations

from decimal import Decimal

import pytest
from django.urls import reverse

from bookstore.cart_store import get_cart, save_cart, clear_cart


pytestmark = pytest.mark.django_db


def _get_customer_id(client_):
    """从已登录 client 的 session 中提取 customer_id。"""
    return client_.session["customer_id"]


def _seed_cart(client_, isbn, qty):
    """通过 cache 预填购物车数据（替代旧的 session 方式）。"""
    cid = _get_customer_id(client_)
    save_cart(cid, {isbn: {"quantity": qty}})


# ----------------------------- cart_add -----------------------------

class TestCartAdd:

    def test_add_first_time_default_quantity_one(self, logged_client, book):
        """TC-CART-001 等价类：GET 请求（无 POST quantity）默认加入 1 件。"""
        url = reverse("bookstore:cart_add", args=[book.isbn])
        resp = logged_client.get(url)
        assert resp.status_code == 302
        cart = get_cart(_get_customer_id(logged_client))
        assert cart[book.isbn]["quantity"] == 1

    def test_add_post_quantity_two(self, logged_client, book):
        """等价类：POST quantity=2 → 购物车有 2 件。"""
        url = reverse("bookstore:cart_add", args=[book.isbn])
        resp = logged_client.post(url, {"quantity": 2})
        assert resp.status_code == 302
        cart = get_cart(_get_customer_id(logged_client))
        assert cart[book.isbn]["quantity"] == 2

    @pytest.mark.parametrize(
        "raw_quantity, expected",
        [
            (0, 1),      # TC-CART-002 边界：0 被修正为 1
            (-5, 1),     # 边界：负数被修正为 1
            ("abc", 1),  # TC-CART-003 异常：非数字回退为 1
            ("", 1),     # 异常：空字符串回退为 1
        ],
    )
    def test_add_invalid_quantity_falls_back_to_one(self, logged_client, book, raw_quantity, expected):
        url = reverse("bookstore:cart_add", args=[book.isbn])
        resp = logged_client.post(url, {"quantity": raw_quantity})
        assert resp.status_code == 302
        cart = get_cart(_get_customer_id(logged_client))
        assert cart[book.isbn]["quantity"] == expected

    def test_add_duplicate_accumulates(self, logged_client, book):
        """TC-CART-004 场景：同一 ISBN 重复加入，数量累加。"""
        url = reverse("bookstore:cart_add", args=[book.isbn])
        logged_client.post(url, {"quantity": 2})
        logged_client.post(url, {"quantity": 3})
        cart = get_cart(_get_customer_id(logged_client))
        assert cart[book.isbn]["quantity"] == 5

    def test_add_requires_login(self, client, book):
        """TC-CART-005 异常：未登录 → 重定向登录页。"""
        url = reverse("bookstore:cart_add", args=[book.isbn])
        resp = client.post(url, {"quantity": 1})
        assert resp.status_code == 302
        assert reverse("bookstore:login") in resp["Location"]

    def test_add_nonexistent_isbn_returns_404(self, logged_client):
        """TC-CART-006 异常：不存在的 ISBN → 404。"""
        url = reverse("bookstore:cart_add", args=["NO_SUCH_ISBN_XXX"])
        resp = logged_client.post(url, {"quantity": 1})
        assert resp.status_code == 404


# ----------------------------- cart_update -----------------------------

class TestCartUpdate:

    def test_update_positive_quantity(self, logged_client, book):
        """TC-CART-007 等价类：更新为 5（独立路径 Path-1：quantity>0）。"""
        _seed_cart(logged_client, book.isbn, 1)
        url = reverse("bookstore:cart_update", args=[book.isbn])
        resp = logged_client.post(url, {"quantity": 5})
        assert resp.status_code == 302
        cart = get_cart(_get_customer_id(logged_client))
        assert cart[book.isbn]["quantity"] == 5

    def test_update_quantity_zero_removes_item(self, logged_client, book):
        """TC-CART-008 边界：quantity=0 → 从购物车移除（独立路径 Path-2）。"""
        _seed_cart(logged_client, book.isbn, 3)
        url = reverse("bookstore:cart_update", args=[book.isbn])
        resp = logged_client.post(url, {"quantity": 0})
        assert resp.status_code == 302
        cart = get_cart(_get_customer_id(logged_client))
        assert book.isbn not in cart

    def test_update_quantity_invalid(self, logged_client, book):
        """TC-CART-009 异常：非法字符串 → 购物车不变（独立路径 Path-3）。"""
        _seed_cart(logged_client, book.isbn, 3)
        url = reverse("bookstore:cart_update", args=[book.isbn])
        resp = logged_client.post(url, {"quantity": "xyz"})
        assert resp.status_code == 302
        cart = get_cart(_get_customer_id(logged_client))
        assert cart[book.isbn]["quantity"] == 3

    def test_update_get_does_nothing(self, logged_client, book):
        """GET 方法不应修改购物车，仅重定向到详情页。"""
        _seed_cart(logged_client, book.isbn, 2)
        url = reverse("bookstore:cart_update", args=[book.isbn])
        resp = logged_client.get(url)
        assert resp.status_code == 302
        cart = get_cart(_get_customer_id(logged_client))
        assert cart[book.isbn]["quantity"] == 2

    def test_update_zero_on_empty_cart_does_not_crash(self, logged_client, book):
        """边界：对空购物车 update quantity=0 也不应报错。"""
        url = reverse("bookstore:cart_update", args=[book.isbn])
        resp = logged_client.post(url, {"quantity": 0})
        assert resp.status_code == 302


# ----------------------------- cart_remove -----------------------------

class TestCartRemove:

    def test_remove_existing_item(self, logged_client, book):
        """TC-CART-010 等价类：删除存在的商品。"""
        _seed_cart(logged_client, book.isbn, 2)

        url = reverse("bookstore:cart_remove", args=[book.isbn])
        resp = logged_client.get(url)
        assert resp.status_code == 302
        cart = get_cart(_get_customer_id(logged_client))
        assert book.isbn not in cart

    def test_remove_nonexistent_item_silent(self, logged_client, book):
        """TC-CART-011 边界：删除不存在的 ISBN，应静默不报错。"""
        url = reverse("bookstore:cart_remove", args=[book.isbn])
        resp = logged_client.get(url)
        assert resp.status_code == 302


# ----------------------------- cart_detail -----------------------------

class TestCartDetail:

    def test_cart_detail_two_items_with_level1_discount(self, logged_client, customer, book, book2):
        """TC-CART-012 场景：2 商品 + 1 级 10% 折扣，折扣金额计算正确。"""
        cid = _get_customer_id(logged_client)
        save_cart(cid, {
            book.isbn: {"quantity": 2},
            book2.isbn: {"quantity": 1},
        })

        url = reverse("bookstore:cart_detail")
        resp = logged_client.get(url)
        assert resp.status_code == 200
        ctx = resp.context

        original_total = Decimal("80") * 2 + Decimal("120")  # 280
        expected_discounted = original_total * Decimal("0.90")  # 252
        expected_discount_amount = original_total - expected_discounted  # 28

        assert ctx["original_total"] == original_total
        assert ctx["discounted_total"] == expected_discounted
        assert ctx["discount_amount"] == expected_discount_amount
        assert ctx["discount_rate"] == Decimal("0.90")
        assert len(ctx["items"]) == 2

    def test_cart_detail_empty_cart(self, logged_client):
        """TC-CART-013 边界：空购物车，items 为空，total=0。"""
        url = reverse("bookstore:cart_detail")
        resp = logged_client.get(url)
        assert resp.status_code == 200
        assert resp.context["items"] == []
        assert resp.context["original_total"] == Decimal("0")
        assert resp.context["discounted_total"] == Decimal("0")

    def test_cart_detail_level3_customer_discount(self, logged_client_l3, customer_l3, book):
        """场景：3 级客户 85% 折扣率。"""
        cid = _get_customer_id(logged_client_l3)
        save_cart(cid, {book.isbn: {"quantity": 1}})

        url = reverse("bookstore:cart_detail")
        resp = logged_client_l3.get(url)
        assert resp.status_code == 200
        assert resp.context["discount_rate"] == Decimal("0.85")
        assert resp.context["discounted_total"] == Decimal("80") * Decimal("0.85")

    def test_cart_detail_requires_login(self, client):
        """异常：未登录访问购物车 → 重定向登录页。"""
        url = reverse("bookstore:cart_detail")
        resp = client.get(url)
        assert resp.status_code == 302
        assert reverse("bookstore:login") in resp["Location"]

    def test_cart_detail_with_base64_cover_image(self, logged_client, db):
        """分支覆盖：book.coverimage 有 base64 字符串时的渲染路径。"""
        from bookstore.models import Book

        # coverimage 是长度 > 50 的 base64 字符串
        fake_b64 = "A" * 100
        b = Book.objects.create(
            isbn="9787000111222",
            title="封面测试书",
            publisher="测试出版社",
            price=Decimal("50.00"),
            keywords="test",
            stockqty=10,
            minstocklimit=2,
            coverimage=fake_b64,
        )
        cid = _get_customer_id(logged_client)
        save_cart(cid, {b.isbn: {"quantity": 1}})

        url = reverse("bookstore:cart_detail")
        resp = logged_client.get(url)
        assert resp.status_code == 200


class TestCartAddReferer:
    """cart_add 的 referer 重定向分支（283 行）。"""

    def test_add_redirects_back_to_referer(self, logged_client, book):
        """当 HTTP_REFERER 非购物车页时，应重定向回该 referer。"""
        url = reverse("bookstore:cart_add", args=[book.isbn])
        resp = logged_client.post(
            url,
            {"quantity": 1},
            HTTP_REFERER="http://testserver/book/" + book.isbn + "/",
        )
        assert resp.status_code == 302
        assert "/book/" in resp["Location"]
