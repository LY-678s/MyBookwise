"""Persistent customer tokens for the mobile API.

Tokens are stored in MySQL instead of Django's local memory cache so every
Gunicorn worker can authenticate the same app session.
"""

from __future__ import annotations

import secrets

from django.db import connection
from django.db.utils import ProgrammingError
from django.utils import timezone

from bookstore.models import CustomerAuthToken

_TABLE_READY = False


def _ensure_token_table() -> None:
    global _TABLE_READY
    if _TABLE_READY:
        return
    table_name = CustomerAuthToken._meta.db_table
    if table_name not in connection.introspection.table_names():
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(CustomerAuthToken)
    _TABLE_READY = True


def create_token(customer_id: int) -> str:
    """Issue a new token and revoke previous tokens for this customer."""

    _ensure_token_table()
    revoke_tokens_for_customer(customer_id)
    token = secrets.token_hex(20)
    CustomerAuthToken.objects.create(token=token, customer_id=customer_id)
    return token


def get_customer_id(token: str) -> int | None:
    """Resolve a token to customer_id; return None when it is invalid."""

    if not token:
        return None
    _ensure_token_table()
    try:
        record = CustomerAuthToken.objects.filter(token=token).only("customer_id").first()
    except ProgrammingError:
        _ensure_token_table()
        record = CustomerAuthToken.objects.filter(token=token).only("customer_id").first()
    if record is None:
        return None
    CustomerAuthToken.objects.filter(token=token).update(last_used_at=timezone.now())
    return record.customer_id


def revoke_token(token: str) -> None:
    """Delete a single token during logout."""

    if token:
        _ensure_token_table()
        CustomerAuthToken.objects.filter(token=token).delete()


def revoke_tokens_for_customer(customer_id: int) -> None:
    """Delete all tokens for a customer before issuing a new one."""

    _ensure_token_table()
    CustomerAuthToken.objects.filter(customer_id=customer_id).delete()
