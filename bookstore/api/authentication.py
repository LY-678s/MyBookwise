"""Token authentication for the mobile API.

Invalid or expired tokens are treated as anonymous requests. Endpoints that
really require login are still protected by IsCustomer, while public endpoints
such as book lists and search continue to work after a database/token reset.
"""

from rest_framework.authentication import BaseAuthentication

from bookstore.models import Customer

from .auth_tokens import get_customer_id


class CustomerTokenAuthentication(BaseAuthentication):
    """Resolve ``Authorization: Token xxx`` into a Customer instance."""

    keyword = "Token"

    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith(f"{self.keyword} "):
            return None

        token = auth_header[len(self.keyword) + 1 :].strip()
        customer_id = get_customer_id(token)
        if customer_id is None:
            return None

        try:
            customer = Customer.objects.select_related("levelid").get(pk=customer_id)
        except Customer.DoesNotExist:
            return None

        return (customer, token)

    def authenticate_header(self, request):
        return self.keyword
