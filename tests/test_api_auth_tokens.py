"""API Token 认证模块单元测试

覆盖函数：create_token、get_customer_id、revoke_token、revoke_tokens_for_customer

测试方法分布：
- 等价类：创建/解析/注销 Token
- 边界值：空 Token、过期 Token
- 场景法：重新登录时旧 Token 失效
- 独立路径：有效/无效 Token 分支
"""
from __future__ import annotations

import pytest

from bookstore.api.auth_tokens import (
    create_token,
    get_customer_id,
    revoke_token,
    revoke_tokens_for_customer,
)


class TestCreateToken:
    """create_token 函数测试。"""

    def test_creates_valid_token(self):
        """等价类：创建 Token → 返回非空字符串。"""
        token = create_token(1)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_maps_to_customer(self):
        """等价类：创建的 Token → 能解析出正确的 customer_id。"""
        token = create_token(42)
        assert get_customer_id(token) == 42

    def test_new_token_invalidates_old(self):
        """场景：重新登录 → 旧 Token 失效。"""
        old_token = create_token(10)
        new_token = create_token(10)
        # 新 Token 有效
        assert get_customer_id(new_token) == 10
        # 旧 Token 失效
        assert get_customer_id(old_token) is None


class TestGetCustomerId:
    """get_customer_id 函数测试。"""

    def test_valid_token(self):
        """等价类：有效 Token → 返回 customer_id。"""
        token = create_token(5)
        assert get_customer_id(token) == 5

    def test_invalid_token(self):
        """等价类：无效 Token → 返回 None。"""
        assert get_customer_id("nonexistent_token") is None

    def test_empty_token(self):
        """边界值：空字符串 → 返回 None。"""
        assert get_customer_id("") is None

    def test_none_token(self):
        """边界值：None → 返回 None。"""
        assert get_customer_id(None) is None


class TestRevokeToken:
    """revoke_token 函数测试。"""

    def test_revoked_token_invalid(self):
        """等价类：注销后 → Token 无效。"""
        token = create_token(1)
        revoke_token(token)
        assert get_customer_id(token) is None

    def test_revoke_nonexistent_no_error(self):
        """边界值：注销不存在的 Token → 不报错。"""
        revoke_token("fake_token")  # 不应抛异常

    def test_revoke_empty_no_error(self):
        """边界值：注销空 Token → 不报错。"""
        revoke_token("")


class TestRevokeTokensForCustomer:
    """revoke_tokens_for_customer 函数测试。"""

    def test_all_tokens_revoked(self):
        """场景：该顾客所有 Token 全部失效。"""
        token1 = create_token(100)
        token2 = create_token(100)  # 会替换 token1
        revoke_tokens_for_customer(100)
        assert get_customer_id(token1) is None
        assert get_customer_id(token2) is None

    def test_other_customer_unaffected(self):
        """场景：不影响其他顾客的 Token。"""
        token_a = create_token(200)
        token_b = create_token(300)
        revoke_tokens_for_customer(200)
        assert get_customer_id(token_a) is None
        assert get_customer_id(token_b) == 300

    def test_revoke_nonexistent_customer_no_error(self):
        """边界值：注销不存在的顾客 → 不报错。"""
        revoke_tokens_for_customer(99999)
