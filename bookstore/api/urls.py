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
    path("books/search/history/", views.SearchHistoryClearView.as_view(), name="search-history-clear"),
    path("books/<str:isbn>/cover/", views.BookCoverView.as_view(), name="book-cover"),
    path("books/<str:isbn>/favorite/", views.BookFavoriteToggleView.as_view(), name="book-favorite-toggle"),
    path("books/<str:isbn>/", views.BookDetailView.as_view(), name="book-detail"),
    path("categories/", views.CategoryListView.as_view(), name="categories"),
    path("rankings/", views.RankingsView.as_view(), name="rankings"),
    path("favorites/folders/", views.FavoriteFolderListView.as_view(), name="favorite-folders"),
    path(
        "favorites/folders/<int:folder_id>/",
        views.FavoriteFolderDeleteView.as_view(),
        name="favorite-folder-delete",
    ),
    # 购物车
    path("cart/", views.CartView.as_view(), name="cart"),
    path("cart/items/", views.CartItemView.as_view(), name="cart-item-add"),
    path("cart/items/<str:isbn>/", views.CartItemView.as_view(), name="cart-item"),
    # 订单
    path("orders/preview/", views.OrderPreviewView.as_view(), name="order-preview"),
    path("orders/", views.OrderListCreateView.as_view(), name="order-list"),
    path("orders/<int:order_id>/", views.OrderDetailView.as_view(), name="order-detail"),
    path("orders/<int:order_id>/abandon/", views.OrderAbandonView.as_view(), name="order-abandon"),
    path(
        "orders/<int:order_id>/sync-payment/",
        views.OrderSyncPaymentView.as_view(),
        name="order-sync-payment",
    ),
    path("orders/<int:order_id>/pay/", views.OrderPayView.as_view(), name="order-pay"),
    path("orders/<int:order_id>/cancel/", views.OrderCancelView.as_view(), name="order-cancel"),
    path(
        "orders/<int:order_id>/confirm-receipt/",
        views.OrderConfirmReceiptView.as_view(),
        name="order-confirm-receipt",
    ),
    # 账户 / 会员
    path("account/", views.AccountView.as_view(), name="account"),
    path("account/repay/", views.AccountRepayView.as_view(), name="account-repay"),
    path("account/browse-history/", views.BrowseHistoryView.as_view(), name="browse-history"),
    path("membership/activate/", views.MembershipActivateView.as_view(), name="membership-activate"),
    path("membership/checkout/", views.MembershipCheckoutView.as_view(), name="membership-checkout"),
    path("membership/confirm/", views.MembershipConfirmView.as_view(), name="membership-confirm"),
    path("payments/stripe/webhook/", views.StripeWebhookView.as_view(), name="stripe-webhook"),
    # AI 助手 — 对应 views.ai_chat / ai_chat_api / ai_chat_clear
    path("ai/", views.AiChatView.as_view(), name="ai-status"),
    path("ai/chat/", views.AiChatView.as_view(), name="ai-chat"),
    path("ai/clear/", views.AiClearView.as_view(), name="ai-clear"),
]
