"""购物车存储模块单元测试

覆盖函数：get_cart、save_cart、clear_cart

测试方法分布：
- 等价类：正常读写、空购物车
- 边界值：多商品、数量累加
- 场景法：购物车完整生命周期
- 独立路径：不同顾客隔离
"""
from __future__ import annotations

import pytest

from bookstore.cart_store import get_cart, save_cart, clear_cart


pytestmark = pytest.mark.django_db


class TestGetCart:
    """get_cart 函数测试。"""

    def test_empty_cart_returns_empty_dict(self):
        """等价类：无购物车 → 返回空字典。"""
        result = get_cart(99999)
        assert result == {}

    def test_returns_saved_cart(self):
        """等价类：保存后读取 → 数据一致。"""
        save_cart(1, {"9787111111": {"quantity": 2}})
        result = get_cart(1)
        assert result == {"9787111111": {"quantity": 2}}


class TestSaveCart:
    """save_cart 函数测试。"""

    def test_overwrites_existing(self):
        """场景：重复保存 → 后值覆盖前值。"""
        save_cart(2, {"A": {"quantity": 1}})
        save_cart(2, {"B": {"quantity": 3}})
        result = get_cart(2)
        assert "A" not in result
        assert result["B"]["quantity"] == 3

    def test_multiple_items(self):
        """边界值：多商品购物车。"""
        cart = {
            "ISBN1": {"quantity": 1},
            "ISBN2": {"quantity": 2},
            "ISBN3": {"quantity": 3},
        }
        save_cart(3, cart)
        result = get_cart(3)
        assert len(result) == 3
        assert result["ISBN2"]["quantity"] == 2


class TestClearCart:
    """clear_cart 函数测试。"""

    def test_clear_removes_cart(self):
        """场景：清空购物车后 → 返回空字典。"""
        save_cart(4, {"ISBN": {"quantity": 5}})
        clear_cart(4)
        assert get_cart(4) == {}

    def test_clear_nonexistent_cart_no_error(self):
        """边界值：清空不存在的购物车 → 不报错。"""
        clear_cart(99999)  # 不应抛异常


class TestCartIsolation:
    """不同顾客购物车隔离。"""

    def test_different_customers_isolated(self):
        """场景：不同顾客的购物车互不影响。"""
        save_cart(10, {"A": {"quantity": 1}})
        save_cart(20, {"B": {"quantity": 2}})
        assert get_cart(10) == {"A": {"quantity": 1}}
        assert get_cart(20) == {"B": {"quantity": 2}}

    def test_clear_one_does_not_affect_other(self):
        """场景：清空一个顾客的购物车，不影响另一个。"""
        save_cart(10, {"A": {"quantity": 1}})
        save_cart(20, {"B": {"quantity": 2}})
        clear_cart(10)
        assert get_cart(10) == {}
        assert get_cart(20) == {"B": {"quantity": 2}}
