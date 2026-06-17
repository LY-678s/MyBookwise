"""
API 路由表 — 前缀 /api/

与 Web 路由对照见各 path 注释；完整说明见 docs/API.md
"""
from django.urls import path

from . import views

app_name = "api"

urlpatterns = [
    # 认证
    path("auth/login/", views.LoginView.as_view(), name="login"),
    path("auth/register/", views.RegisterView.as_view(), name="register"),
    path("auth/logout/", views.LogoutView.as_view(), name="logout"),
    path("auth/me/", views.MeView.as_view(), name="me"),
    # 图书（无需登录）
    path("books/", views.BookListView.as_view(), name="book-list"),
    path("books/search/", views.BookSearchView.as_view(), name="book-search"),
    path("books/<str:isbn>/", views.BookDetailView.as_view(), name="book-detail"),
    # 购物车
    path("cart/", views.CartView.as_view(), name="cart"),
    path("cart/items/", views.CartItemView.as_view(), name="cart-item-add"),
    path("cart/items/<str:isbn>/", views.CartItemView.as_view(), name="cart-item"),
    # 订单
    path("orders/preview/", views.OrderPreviewView.as_view(), name="order-preview"),
    path("orders/", views.OrderListCreateView.as_view(), name="order-list"),
    path("orders/<int:order_id>/", views.OrderDetailView.as_view(), name="order-detail"),
    path("orders/<int:order_id>/pay/", views.OrderPayView.as_view(), name="order-pay"),
    path("orders/<int:order_id>/cancel/", views.OrderCancelView.as_view(), name="order-cancel"),
    path(
        "orders/<int:order_id>/confirm-receipt/",
        views.OrderConfirmReceiptView.as_view(),
        name="order-confirm-receipt",
    ),
    # 账户
    path("account/", views.AccountView.as_view(), name="account"),
    path("account/recharge/", views.AccountRechargeView.as_view(), name="account-recharge"),
    path("account/repay/", views.AccountRepayView.as_view(), name="account-repay"),
]
