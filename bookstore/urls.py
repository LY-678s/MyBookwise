from django.urls import path
from . import views

app_name = "bookstore"

urlpatterns = [
    path("", views.index, name="index"),   # 首页：图书列表
    path("book/<str:isbn>/", views.book_detail, name="book_detail"),
    path("search/", views.search, name="search"),

    # 顾客登录 / 注销
    path("login/", views.customer_login, name="login"),
    path("logout/", views.customer_logout, name="logout"),

    # 购物车 & 下单
    path("cart/", views.cart_detail, name="cart_detail"),
    path("cart/add/<str:isbn>/", views.cart_add, name="cart_add"),
    path("cart/remove/<str:isbn>/", views.cart_remove, name="cart_remove"),
    path("order/confirm/", views.order_confirm, name="order_confirm"),
    path("orders/", views.order_list, name="order_list"),
    path("orders/<int:order_id>/", views.order_detail, name="order_detail"),
]