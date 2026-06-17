"""
DRF 认证：将 Authorization: Token xxx 解析为 Customer 实例。

authenticate 返回 (customer, token)，DRF 会把 customer 赋给 request.user。
各需登录接口配合 permissions.IsCustomer 使用。
"""
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from bookstore.models import Customer

from .auth_tokens import get_customer_id


class CustomerTokenAuthentication(BaseAuthentication):
    """对应 Web 端 session['customer_id'] 的 APP 替代方案。"""

    keyword = "Token"

    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith(f"{self.keyword} "):
            return None  # 未携带 Token，交给 AllowAny / IsCustomer 处理

        token = auth_header[len(self.keyword) + 1 :].strip()
        customer_id = get_customer_id(token)
        if customer_id is None:
            raise AuthenticationFailed("无效或已过期的登录令牌，请重新登录")

        try:
            customer = Customer.objects.select_related("levelid").get(pk=customer_id)
        except Customer.DoesNotExist as exc:
            raise AuthenticationFailed("用户不存在") from exc

        return (customer, token)

    def authenticate_header(self, request):
        return self.keyword
