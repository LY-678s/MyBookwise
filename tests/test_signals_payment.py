"""
单元测试模块 - bookstore.signals 支付与订单模块

本模块测试 signals.py 中的核心函数：
1. complete_order_payment() - Stripe 支付成功后处理
2. _get_old_order_values() - 获取订单旧值
3. _handle_deduct_or_refund() - 订单取消退款处理（积分扣回）

测试方法：边界值测试、等价类测试、场景法、独立路径测试
"""
import os
import sys
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch, PropertyMock, sentinel
from contextlib import contextmanager

import pytest

# 配置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MyBookwise.settings')


# =============================================================================
# 辅助函数：创建Mock上下文管理器
# =============================================================================

@contextmanager
def mock_transaction_atomic():
    """Mock transaction.atomic 上下文管理器"""
    yield


@contextmanager
def mock_atomic_with_rollback():
    """Mock transaction.atomic 并执行回滚"""
    yield


# =============================================================================
# 测试类1: _get_old_order_values 订单旧值获取函数测试
# =============================================================================

class TestGetOldOrderValues:
    """
    测试 _get_old_order_values 函数

    函数逻辑：
    - 新建订单（无pk）：返回 (None, None)
    - 存在的订单：返回 (old_status, old_totalamount)
    - 不存在的订单：返回 (None, None)
    """

    # ------------------- 场景法测试 (Scenario Testing) -------------------

    @pytest.mark.unit
    @pytest.mark.scenario
    def test_scenario_new_order(self):
        """场景1：新建订单（无pk）"""
        from bookstore.signals import _get_old_order_values
        mock_instance = Mock()
        mock_instance.pk = None

        status, total = _get_old_order_values(mock_instance)

        assert status is None
        assert total is None

    @pytest.mark.unit
    @pytest.mark.scenario
    def test_scenario_existing_order(self):
        """场景2：已存在的订单"""
        from bookstore.signals import _get_old_order_values

        mock_instance = Mock()
        mock_instance.pk = 1

        with patch('bookstore.signals.Orders') as mock_orders:
            mock_order = Mock()
            mock_order.status = 0
            mock_order.totalamount = Decimal('100.00')
            mock_orders.objects.get.return_value = mock_order

            status, total = _get_old_order_values(mock_instance)

            assert status == 0
            assert total == Decimal('100.00')
            mock_orders.objects.get.assert_called_once_with(pk=1)

    @pytest.mark.unit
    @pytest.mark.scenario
    def test_scenario_order_not_found(self):
        """场景3：订单不存在（被删除）- 返回None"""
        from bookstore.signals import _get_old_order_values
        from django.core.exceptions import ObjectDoesNotExist

        mock_instance = Mock()
        mock_instance.pk = 999

        with patch('bookstore.signals.Orders') as mock_orders:
            class MockDoesNotExist(ObjectDoesNotExist):
                pass

            mock_orders.DoesNotExist = MockDoesNotExist
            mock_orders.objects.get.side_effect = MockDoesNotExist()

            status, total = _get_old_order_values(mock_instance)

            assert status is None
            assert total is None

    # ------------------- 等价类测试 -------------------

    @pytest.mark.unit
    @pytest.mark.equivalence
    @pytest.mark.parametrize("pk_value,should_call_get", [
        (None, False),                 # 无pk：不需要查询
        (0, False),                    # pk=0：无效pk
        (1, True),                    # 有效pk：需要查询
        (100, True),                  # 任意有效pk
    ])
    def test_equivalence_classes(self, pk_value, should_call_get):
        """等价类测试：不同pk值的处理"""
        from bookstore.signals import _get_old_order_values

        mock_instance = Mock()
        mock_instance.pk = pk_value

        with patch('bookstore.signals.Orders') as mock_orders:
            if should_call_get:
                mock_order = Mock()
                mock_order.status = 1
                mock_order.totalamount = Decimal('200.00')
                mock_orders.objects.get.return_value = mock_order

            status, total = _get_old_order_values(mock_instance)

            if should_call_get:
                mock_orders.objects.get.assert_called_once()
            else:
                mock_orders.objects.get.assert_not_called()


# =============================================================================
# 测试类2: complete_order_payment 支付成功处理函数测试
# =============================================================================

class TestCompleteOrderPayment:
    """
    测试 complete_order_payment 函数

    函数逻辑：
    - 标记订单已付款（paymentstatus=1）
    - 设置 actualpaid = totalamount
    - 会员累计积分（1:1）
    - 非会员不累计积分
    """

    def _create_mock_order(self, totalamount=Decimal('100.00')):
        """创建模拟订单对象"""
        order = Mock()
        order.totalamount = totalamount
        order.actualpaid = Decimal('0.00')
        order.paymentstatus = 0
        return order

    def _create_mock_customer(self, customerid=1):
        """创建模拟客户对象"""
        customer = Mock()
        customer.customerid = customerid
        return customer

    # ------------------- 场景法测试 -------------------

    @pytest.mark.unit
    @pytest.mark.scenario
    def test_scenario_member_payment(self):
        """场景1：会员支付成功，累计积分"""
        from bookstore.signals import complete_order_payment

        order = self._create_mock_order(totalamount=Decimal('200.00'))
        customer = self._create_mock_customer(customerid=1)

        with patch('bookstore.membership.is_member', return_value=True), \
             patch('bookstore.membership.award_order_points') as mock_award:
            result = complete_order_payment(order, customer)

        assert order.paymentstatus == 1
        assert order.actualpaid == Decimal('200.00')
        mock_award.assert_called_once_with(1, Decimal('200.00'))
        assert '积分已累计' in result

    @pytest.mark.unit
    @pytest.mark.scenario
    def test_scenario_non_member_payment(self):
        """场景2：非会员支付成功，不累计积分"""
        from bookstore.signals import complete_order_payment

        order = self._create_mock_order(totalamount=Decimal('150.00'))
        customer = self._create_mock_customer(customerid=2)

        with patch('bookstore.membership.is_member', return_value=False), \
             patch('bookstore.membership.award_order_points') as mock_award:
            result = complete_order_payment(order, customer)

        assert order.paymentstatus == 1
        assert order.actualpaid == Decimal('150.00')
        mock_award.assert_not_called()
        assert '积分' not in result

    @pytest.mark.unit
    @pytest.mark.scenario
    def test_scenario_zero_amount(self):
        """场景3：零金额订单"""
        from bookstore.signals import complete_order_payment

        order = self._create_mock_order(totalamount=Decimal('0.00'))
        customer = self._create_mock_customer(customerid=1)

        with patch('bookstore.membership.is_member', return_value=True), \
             patch('bookstore.membership.award_order_points') as mock_award:
            result = complete_order_payment(order, customer)

        assert order.paymentstatus == 1
        assert order.actualpaid == Decimal('0.00')
        mock_award.assert_called_once_with(1, Decimal('0.00'))


# =============================================================================
# 测试类3: _handle_deduct_or_refund 订单取消退款处理函数测试
# =============================================================================

class TestHandleDeductOrRefund:
    """
    测试 _handle_deduct_or_refund 函数

    订单状态流转：
    - status=0: 待付款
    - status=1: 已付款/待发货
    - status=2: 已完成
    - status=4: 已取消

    测试场景：
    1. 订单取消(status=4)：触发积分扣回（会员）
    2. 订单完成(status=2)：无额外操作
    3. 状态不变：不处理
    """

    def _create_mock_instance(self, status=0, totalamount=Decimal('100.00'),
                              actualpaid=Decimal('0.00'), paymentstatus=0,
                              orderid=1, customerid_id=1):
        """创建模拟订单实例"""
        instance = Mock()
        instance.status = status
        instance.totalamount = totalamount
        instance.actualpaid = actualpaid
        instance.paymentstatus = paymentstatus
        instance.orderid = orderid
        instance.customerid_id = customerid_id
        return instance

    def _create_mock_customer(self, customerid=1, levelid=2):
        """创建模拟客户"""
        customer = Mock()
        customer.customerid = customerid
        customer.levelid = Mock()
        customer.levelid.levelid = levelid
        return customer

    # ------------------- 场景法测试 -------------------

    @pytest.mark.unit
    @pytest.mark.scenario
    def test_scenario_order_cancel_refund_member(self):
        """场景1：会员订单取消 - 扣回积分"""
        from bookstore.signals import _handle_deduct_or_refund

        instance = self._create_mock_instance(
            status=4,
            totalamount=Decimal('200.00'),
            actualpaid=Decimal('200.00'),
            paymentstatus=1
        )
        old_status = 0

        mock_customer = self._create_mock_customer(customerid=1, levelid=2)

        with patch('bookstore.signals.Customer') as mock_customer_class, \
             patch('bookstore.membership.is_member', return_value=True), \
             patch('bookstore.membership.get_profile') as mock_get_profile, \
             patch('bookstore.membership.sync_member_level') as mock_sync, \
             patch('bookstore.signals.transaction.atomic', return_value=mock_transaction_atomic()):

            mock_profile = Mock()
            mock_profile.points = 500
            mock_get_profile.return_value = mock_profile

            mock_customer_class.objects.select_for_update.return_value.select_related.return_value.get.return_value = mock_customer

            _handle_deduct_or_refund(instance, old_status, Decimal('200.00'))

        assert mock_profile.points == 300  # 500 - 200
        assert instance.paymentstatus == 3
        mock_sync.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.scenario
    def test_scenario_order_cancel_non_member(self):
        """场景2：非会员订单取消 - 不扣积分"""
        from bookstore.signals import _handle_deduct_or_refund

        instance = self._create_mock_instance(
            status=4,
            totalamount=Decimal('200.00'),
            actualpaid=Decimal('200.00'),
            paymentstatus=1
        )
        old_status = 0

        mock_customer = self._create_mock_customer(customerid=2, levelid=0)

        with patch('bookstore.signals.Customer') as mock_customer_class, \
             patch('bookstore.membership.is_member', return_value=False), \
             patch('bookstore.signals.transaction.atomic', return_value=mock_transaction_atomic()):

            mock_customer_class.objects.select_for_update.return_value.select_related.return_value.get.return_value = mock_customer

            _handle_deduct_or_refund(instance, old_status, Decimal('200.00'))

        assert instance.paymentstatus == 3

    @pytest.mark.unit
    @pytest.mark.scenario
    def test_scenario_order_complete(self):
        """场景3：订单完成 - 无额外操作"""
        from bookstore.signals import _handle_deduct_or_refund

        instance = self._create_mock_instance(status=2)
        old_status = 1

        mock_customer = self._create_mock_customer()

        with patch('bookstore.signals.Customer') as mock_customer_class, \
             patch('bookstore.signals.transaction.atomic', return_value=mock_transaction_atomic()):
            mock_customer_class.objects.select_for_update.return_value.select_related.return_value.get.return_value = mock_customer

            _handle_deduct_or_refund(instance, old_status, Decimal('100.00'))

    @pytest.mark.unit
    @pytest.mark.scenario
    def test_scenario_status_unchanged(self):
        """场景4：状态未变化 - 不处理"""
        from bookstore.signals import _handle_deduct_or_refund

        instance = self._create_mock_instance(status=0)
        old_status = 0

        mock_customer = self._create_mock_customer()

        with patch('bookstore.signals.Customer') as mock_customer_class, \
             patch('bookstore.signals.transaction.atomic', return_value=mock_transaction_atomic()):
            mock_customer_class.objects.select_for_update.return_value.select_related.return_value.get.return_value = mock_customer

            _handle_deduct_or_refund(instance, old_status, Decimal('100.00'))

    # ------------------- 边界值测试 -------------------

    @pytest.mark.unit
    @pytest.mark.boundary
    def test_boundary_zero_amount_cancel(self):
        """边界值测试：零金额订单取消"""
        from bookstore.signals import _handle_deduct_or_refund

        instance = self._create_mock_instance(
            status=4,
            totalamount=Decimal('0.00'),
            actualpaid=Decimal('0.00'),
            paymentstatus=0
        )
        old_status = 0

        mock_customer = self._create_mock_customer()

        with patch('bookstore.signals.Customer') as mock_customer_class, \
             patch('bookstore.membership.is_member', return_value=False), \
             patch('bookstore.signals.transaction.atomic', return_value=mock_transaction_atomic()):
            mock_customer_class.objects.select_for_update.return_value.select_related.return_value.get.return_value = mock_customer

            _handle_deduct_or_refund(instance, old_status, Decimal('0.00'))

        assert instance.paymentstatus == 3

    @pytest.mark.unit
    @pytest.mark.boundary
    def test_boundary_large_amount_refund(self):
        """边界值测试：大金额退款"""
        from bookstore.signals import _handle_deduct_or_refund

        instance = self._create_mock_instance(
            status=4,
            totalamount=Decimal('10000.00'),
            actualpaid=Decimal('10000.00'),
            paymentstatus=1
        )
        old_status = 0

        mock_customer = self._create_mock_customer(customerid=1, levelid=5)

        with patch('bookstore.signals.Customer') as mock_customer_class, \
             patch('bookstore.membership.is_member', return_value=True), \
             patch('bookstore.membership.get_profile') as mock_get_profile, \
             patch('bookstore.membership.sync_member_level') as mock_sync, \
             patch('bookstore.signals.transaction.atomic', return_value=mock_transaction_atomic()):

            mock_profile = Mock()
            mock_profile.points = 15000
            mock_get_profile.return_value = mock_profile

            mock_customer_class.objects.select_for_update.return_value.select_related.return_value.get.return_value = mock_customer

            _handle_deduct_or_refund(instance, old_status, Decimal('10000.00'))

        assert mock_profile.points == 5000  # 15000 - 10000
        assert instance.paymentstatus == 3

    # ------------------- 独立路径测试 -------------------

    @pytest.mark.unit
    @pytest.mark.path
    def test_path_cancel_with_payment(self):
        """独立路径：取消 + 已付款"""
        from bookstore.signals import _handle_deduct_or_refund

        instance = self._create_mock_instance(status=4, actualpaid=Decimal('100.00'), paymentstatus=1)
        mock_customer = self._create_mock_customer(customerid=1)

        with patch('bookstore.signals.Customer') as mock_customer_class, \
             patch('bookstore.membership.is_member', return_value=True), \
             patch('bookstore.membership.get_profile') as mock_get_profile, \
             patch('bookstore.membership.sync_member_level') as mock_sync, \
             patch('bookstore.signals.transaction.atomic', return_value=mock_transaction_atomic()):

            mock_profile = Mock()
            mock_profile.points = 200
            mock_get_profile.return_value = mock_profile

            mock_customer_class.objects.select_for_update.return_value.select_related.return_value.get.return_value = mock_customer

            _handle_deduct_or_refund(instance, 0, Decimal('100.00'))

        assert mock_profile.points == 100  # 200 - 100

    @pytest.mark.unit
    @pytest.mark.path
    def test_path_complete_no_action(self):
        """独立路径：完成订单无操作"""
        from bookstore.signals import _handle_deduct_or_refund

        instance = self._create_mock_instance(status=2)
        mock_customer = self._create_mock_customer()

        with patch('bookstore.signals.Customer') as mock_customer_class, \
             patch('bookstore.signals.transaction.atomic', return_value=mock_transaction_atomic()):
            mock_customer_class.objects.select_for_update.return_value.select_related.return_value.get.return_value = mock_customer

            _handle_deduct_or_refund(instance, 1, Decimal('100.00'))


# =============================================================================
# 测试报告辅助函数
# =============================================================================

def get_test_summary():
    """生成测试摘要信息"""
    return {
        'total_functions': 3,
        'total_test_classes': 3,
        'functions_tested': [
            'complete_order_payment',
            '_get_old_order_values',
            '_handle_deduct_or_refund'
        ],
        'test_methods': [
            'boundary', 'equivalence', 'scenario', 'path'
        ]
    }
