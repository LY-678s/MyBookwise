"""Permissions for the mobile API."""

from rest_framework.permissions import BasePermission

from bookstore.models import Customer

from .debug_logging import logger, request_context


class IsCustomer(BasePermission):
    """Require an authenticated Customer for protected API endpoints."""

    message = "请先登录"

    def has_permission(self, request, view):
        allowed = isinstance(request.user, Customer)
        if not allowed:
            logger.warning(
                "api_permission_denied view=%s context=%s",
                view.__class__.__name__,
                request_context(request),
            )
        return allowed
