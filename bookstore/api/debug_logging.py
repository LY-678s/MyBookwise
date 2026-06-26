"""Request diagnostics for API/auth problems.

The logs are intentionally compact and safe: tokens are masked, but request
path, host, origin and auth state are visible enough to diagnose 401/403 cases.
"""

from __future__ import annotations

import logging
import uuid

from django.core.exceptions import DisallowedHost
from django.views.csrf import csrf_failure as django_csrf_failure

logger = logging.getLogger("bookstore.api")


def mask_token(token: str | None) -> str:
    if not token:
        return "none"
    token = token.strip()
    if len(token) <= 10:
        return "***"
    return f"{token[:6]}...{token[-4:]}"


def get_token_from_request(request) -> str | None:
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if auth_header.startswith("Token "):
        return auth_header[len("Token ") :].strip()
    if auth_header:
        return "unsupported-auth-scheme"
    return None


def get_safe_host(request) -> str:
    try:
        return request.get_host()
    except DisallowedHost as exc:
        return f"disallowed:{request.META.get('HTTP_HOST', '')} ({exc})"


def request_context(request, extra: dict | None = None) -> dict:
    # Do not access request.user here: during authentication that would trigger
    # DRF authentication recursively. Read only the already-resolved private
    # value when it exists.
    user = request.__dict__.get("_user")
    customer_id = getattr(user, "customerid", None)
    token = get_token_from_request(request)
    data = {
        "rid": getattr(request, "mybookwise_request_id", "-"),
        "method": request.method,
        "path": request.get_full_path(),
        "host": get_safe_host(request),
        "origin": request.META.get("HTTP_ORIGIN", ""),
        "referer": request.META.get("HTTP_REFERER", ""),
        "xff": request.META.get("HTTP_X_FORWARDED_FOR", ""),
        "cf_ray": request.META.get("HTTP_CF_RAY", ""),
        "ua": request.META.get("HTTP_USER_AGENT", "")[:120],
        "has_auth": bool(token),
        "token": mask_token(token),
        "customer_id": customer_id,
    }
    if extra:
        data.update(extra)
    return data


class ApiDebugLoggingMiddleware:
    """Attach a request id and log Django-side 401/403 responses."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.mybookwise_request_id = uuid.uuid4().hex[:12]
        response = self.get_response(request)
        response["X-MyBookwise-Request-Id"] = request.mybookwise_request_id

        if response.status_code in (401, 403):
            logger.warning(
                "django_denied status=%s reason=%s context=%s",
                response.status_code,
                getattr(response, "reason_phrase", ""),
                request_context(request),
            )
        return response


def csrf_failure(request, reason=""):
    """Log CSRF failures before returning Django's normal 403 page."""

    logger.warning(
        "csrf_denied reason=%s context=%s",
        reason,
        request_context(request),
    )
    return django_csrf_failure(request, reason=reason)
