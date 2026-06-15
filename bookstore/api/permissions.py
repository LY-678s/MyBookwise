"""API 权限：判断 request.user 是否为已登录的 Customer。"""
from rest_framework.permissions import BasePermission

from bookstore.models import Customer


class IsCustomer(BasePermission):
    """对应 Web 端 @customer_required 装饰器。"""

    message = "请先登录"

    def has_permission(self, request, view):
        return isinstance(request.user, Customer)
