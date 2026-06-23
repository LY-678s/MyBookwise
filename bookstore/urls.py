from django.urls import path

from . import views
from bookstore.api import views as api_views


app_name = "bookstore"

urlpatterns = [
    path("", views.index, name="index"),
    path("book/<str:isbn>/", views.book_detail, name="book_detail"),
    path("book/<str:isbn>/favorite/", views.favorite_toggle, name="favorite_toggle"),
    path("search/", views.search, name="search"),
    path("categories/", views.categories, name="categories"),
    path("rankings/", views.rankings, name="rankings"),

    path("login/", views.customer_login, name="login"),
    path("register/", views.customer_register, name="register"),
    path("logout/", views.customer_logout, name="logout"),

    path("cart/", views.cart_detail, name="cart_detail"),
    path("cart/add/<str:isbn>/", views.cart_add, name="cart_add"),
    path("cart/update/<str:isbn>/", views.cart_update, name="cart_update"),
    path("cart/remove/<str:isbn>/", views.cart_remove, name="cart_remove"),
    path("order/confirm/", views.order_confirm, name="order_confirm"),
    path("orders/", views.order_list, name="order_list"),
    path("orders/<int:order_id>/", views.order_detail, name="order_detail"),
    path("orders/<int:order_id>/pay/", views.pay_order, name="pay_order"),
    path("orders/<int:order_id>/cancel/", views.cancel_order, name="cancel_order"),
    path("orders/<int:order_id>/confirm/", views.confirm_receipt, name="confirm_receipt"),

    path("ai/", views.ai_chat, name="ai_chat"),
    path("ai/chat/", views.ai_chat_api, name="ai_chat_api"),
    path("ai/clear/", views.ai_chat_clear, name="ai_chat_clear"),

    path("account/", views.account_recharge, name="account"),
    path("account/edit/", views.account_edit, name="account_edit"),
    path("account/repay/", views.repay_overdraft, name="repay_overdraft"),
    path("account/favorites/", views.favorite_folders, name="favorite_folders"),
    path("account/favorites/<int:folder_id>/delete/", views.favorite_folder_delete, name="favorite_folder_delete"),

    path("api/books/", api_views.get_books_page, name="api_books"),
]
