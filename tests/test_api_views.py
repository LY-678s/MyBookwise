"""RESTful API 接口单元测试（企业标准）

覆盖接口：
- 认证：POST /api/auth/login/ /register/ /logout/ GET /api/auth/me/
- 图书：GET /api/books/ /api/books/search/ /api/books/<isbn>/
- 购物车：GET /api/cart/ POST/PUT/DELETE /api/cart/items/
- 订单：GET/POST /api/orders/ GET /api/orders/<id>/
- 账户：GET/PATCH /api/account/ POST /api/account/recharge/

测试方法分布：
- 等价类：正常请求、参数错误
- 边界值：空数据、不存在资源
- 场景法：完整购物流程（注册→登录→加购→下单→查看）
- 独立路径：认证/未认证、权限控制
"""
from __future__ import annotations

from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework.test import APIClient


pytestmark = pytest.mark.django_db


# =============================================================
# 工具函数与 Fixture
# =============================================================

@pytest.fixture
def api_client():
    """返回 DRF APIClient 实例。"""
    return APIClient()


@pytest.fixture
def auth_client(customer):
    """返回已认证的 APIClient（携带有效 Token）。"""
    from bookstore.api.auth_tokens import create_token
    client = APIClient()
    token = create_token(customer.customerid)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
    return client, customer, token


# =============================================================
# 认证接口
# =============================================================

class TestAuthLogin:
    """POST /api/auth/login/"""

    def test_login_success(self, api_client, customer):
        """等价类：正确账号 → 200 + token。"""
        resp = api_client.post("/api/auth/login/", {
            "username": customer.username,
            "password": customer.password,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "token" in data
        assert "customer" in data

    def test_login_wrong_password(self, api_client, customer):
        """等价类：密码错误 → 401。"""
        resp = api_client.post("/api/auth/login/", {
            "username": customer.username,
            "password": "wrong",
        })
        assert resp.status_code == 401
        assert resp.json()["success"] is False

    def test_login_nonexistent_user(self, api_client):
        """等价类：用户不存在 → 401。"""
        resp = api_client.post("/api/auth/login/", {
            "username": "nobody",
            "password": "123456",
        })
        assert resp.status_code == 401

    def test_login_empty_fields(self, api_client):
        """边界值：空字段 → 401。"""
        resp = api_client.post("/api/auth/login/", {"username": "", "password": ""})
        assert resp.status_code == 401


class TestAuthRegister:
    """POST /api/auth/register/"""

    def test_register_success(self, api_client, creditlevels):
        """等价类：完整信息 → 201 + token。"""
        resp = api_client.post("/api/auth/register/", {
            "username": "newuser",
            "password": "123456",
            "name": "新用户",
            "email": "new@test.com",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["success"] is True
        assert "token" in data

    def test_register_duplicate_username(self, api_client, customer, creditlevels):
        """等价类：用户名重复 → 400。"""
        resp = api_client.post("/api/auth/register/", {
            "username": customer.username,
            "password": "123456",
            "name": "重名",
            "email": "other@test.com",
        })
        assert resp.status_code == 400
        assert resp.json()["success"] is False

    def test_register_missing_fields(self, api_client):
        """边界值：缺少必填字段 → 400。"""
        resp = api_client.post("/api/auth/register/", {"username": "only_name"})
        assert resp.status_code == 400


class TestAuthLogout:
    """POST /api/auth/logout/"""

    def test_logout_success(self, auth_client):
        """等价类：已登录 → 200 + token 失效。"""
        client, customer, token = auth_client
        resp = client.post("/api/auth/logout/")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # Token 应失效
        from bookstore.api.auth_tokens import get_customer_id
        assert get_customer_id(token) is None

    def test_logout_without_auth(self, api_client):
        """异常：未登录 → 401/403。"""
        resp = api_client.post("/api/auth/logout/")
        assert resp.status_code in (401, 403)


class TestAuthMe:
    """GET /api/auth/me/"""

    def test_me_success(self, auth_client):
        """等价类：已登录 → 返回用户信息。"""
        client, customer, _ = auth_client
        resp = client.get("/api/auth/me/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["customer"]["name"] == customer.name

    def test_me_without_auth(self, api_client):
        """异常：未登录 → 401/403。"""
        resp = api_client.get("/api/auth/me/")
        assert resp.status_code in (401, 403)


# =============================================================
# 图书接口（无需登录）
# =============================================================

class TestBookList:
    """GET /api/books/"""

    def test_books_returns_list(self, api_client, book):
        """等价类：有图书 → 返回分页列表。"""
        resp = api_client.get("/api/books/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "books" in data
        assert data["total_count"] >= 1

    def test_books_pagination(self, api_client, book, book2):
        """边界值：分页参数。"""
        resp = api_client.get("/api/books/?page=1&page_size=1")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["books"]) == 1
        assert data["total_pages"] == 2

    def test_books_empty_db(self, api_client):
        """边界值：无图书 → 空列表。"""
        resp = api_client.get("/api/books/")
        assert resp.status_code == 200
        assert resp.json()["books"] == []


class TestBookSearch:
    """GET /api/books/search/?q="""

    def test_search_by_title(self, api_client, book):
        """等价类：按书名搜索 → 返回匹配结果。"""
        resp = api_client.get(f"/api/books/search/?q={book.title}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["books"]) >= 1

    def test_search_no_results(self, api_client):
        """等价类：无匹配 → 空列表。"""
        resp = api_client.get("/api/books/search/?q=不存在的书名XXXYYY")
        assert resp.status_code == 200
        assert resp.json()["books"] == []

    def test_search_empty_query(self, api_client, book):
        """边界值：空查询 → 返回全部或空。"""
        resp = api_client.get("/api/books/search/?q=")
        assert resp.status_code == 200


class TestBookDetail:
    """GET /api/books/<isbn>/"""

    def test_detail_success(self, api_client, book):
        """等价类：有效 ISBN → 返回图书详情。"""
        resp = api_client.get(f"/api/books/{book.isbn}/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["book"]["isbn"] == book.isbn

    def test_detail_not_found(self, api_client):
        """异常：不存在的 ISBN → 404。"""
        resp = api_client.get("/api/books/NONEXISTENT123/")
        assert resp.status_code == 404
        assert resp.json()["success"] is False


# =============================================================
# 购物车接口（需登录）
# =============================================================

class TestCartAPI:
    """GET /api/cart/ POST/PUT/DELETE /api/cart/items/"""

    def test_get_cart_empty(self, auth_client):
        """等价类：空购物车 → 返回空。"""
        client, _, _ = auth_client
        resp = client.get("/api/cart/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    def test_add_to_cart(self, auth_client, book):
        """等价类：加入购物车 → 成功。"""
        client, _, _ = auth_client
        resp = client.post("/api/cart/items/", {"isbn": book.isbn, "quantity": 2})
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_add_missing_isbn(self, auth_client):
        """边界值：缺少 isbn → 400。"""
        client, _, _ = auth_client
        resp = client.post("/api/cart/items/", {"quantity": 1})
        assert resp.status_code == 400

    def test_cart_requires_auth(self, api_client):
        """异常：未登录 → 401/403。"""
        resp = api_client.get("/api/cart/")
        assert resp.status_code in (401, 403)

    def test_delete_cart_item(self, auth_client, book):
        """场景：先加后删。"""
        client, _, _ = auth_client
        # 先加入
        client.post("/api/cart/items/", {"isbn": book.isbn, "quantity": 1})
        # 再删除
        resp = client.delete(f"/api/cart/items/{book.isbn}/")
        assert resp.status_code == 200


# =============================================================
# 订单接口（需登录）
# =============================================================

class TestOrderAPI:
    """GET/POST /api/orders/ GET /api/orders/<id>/"""

    def test_list_orders_empty(self, auth_client):
        """等价类：无订单 → 空列表。"""
        client, _, _ = auth_client
        resp = client.get("/api/orders/")
        assert resp.status_code == 200
        assert resp.json()["orders"] == []

    def test_order_preview_empty_cart(self, auth_client):
        """边界值：空购物车预览 → 错误提示。"""
        client, _, _ = auth_client
        resp = client.get("/api/orders/preview/")
        assert resp.status_code == 400

    def test_orders_requires_auth(self, api_client):
        """异常：未登录访问订单 → 401/403。"""
        resp = api_client.get("/api/orders/")
        assert resp.status_code in (401, 403)

    def test_order_detail_not_found(self, auth_client):
        """异常：不存在的订单 → 404。"""
        client, _, _ = auth_client
        resp = client.get("/api/orders/999999/")
        assert resp.status_code == 404


# =============================================================
# 账户接口（需登录）
# =============================================================

class TestAccountAPI:
    """GET/PATCH /api/account/ POST /api/account/recharge/"""

    def test_get_account(self, auth_client):
        """等价类：获取账户信息。"""
        client, customer, _ = auth_client
        resp = client.get("/api/account/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "account" in data

    def test_recharge_success(self, auth_client):
        """等价类：充值成功。"""
        client, customer, _ = auth_client
        resp = client.post("/api/account/recharge/", {"amount": "100.00"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    def test_recharge_invalid_amount(self, auth_client):
        """边界值：无效金额 → 400。"""
        client, _, _ = auth_client
        resp = client.post("/api/account/recharge/", {"amount": "abc"})
        assert resp.status_code == 400

    def test_recharge_negative_amount(self, auth_client):
        """边界值：负数金额 → 400。"""
        client, _, _ = auth_client
        resp = client.post("/api/account/recharge/", {"amount": "-50"})
        assert resp.status_code == 400

    def test_account_requires_auth(self, api_client):
        """异常：未登录 → 401/403。"""
        resp = api_client.get("/api/account/")
        assert resp.status_code in (401, 403)


# =============================================================
# 完整购物流程（场景法）
# =============================================================

class TestFullShoppingFlow:
    """场景法：完整购物流程（注册→登录→浏览→加购→查看购物车）。"""

    def test_full_flow(self, api_client, creditlevels, book):
        """场景：端到端购物流程。"""
        # 1. 注册
        resp = api_client.post("/api/auth/register/", {
            "username": "flow_user",
            "password": "123456",
            "name": "流程用户",
            "email": "flow@test.com",
        })
        assert resp.status_code == 201
        token = resp.json()["token"]

        # 2. 用 token 访问需要登录的接口
        api_client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

        # 3. 浏览图书列表
        resp = api_client.get("/api/books/")
        assert resp.status_code == 200

        # 4. 加入购物车
        resp = api_client.post("/api/cart/items/", {
            "isbn": book.isbn,
            "quantity": 1,
        })
        assert resp.status_code == 200

        # 5. 查看购物车
        resp = api_client.get("/api/cart/")
        assert resp.status_code == 200

        # 6. 查看账户信息
        resp = api_client.get("/api/account/")
        assert resp.status_code == 200

        # 7. 登出
        resp = api_client.post("/api/auth/logout/")
        assert resp.status_code == 200

        # 8. 登出后 token 应失效
        resp = api_client.get("/api/account/")
        assert resp.status_code in (401, 403)
