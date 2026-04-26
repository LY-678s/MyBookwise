"""
单元测试模块 - bookstore.signals 支付与信用模块

本模块测试 signals.py 中的4个核心函数：
1. _calculate_credit_level() - 信用等级计算
2. process_payment() - 支付处理
3. _get_old_order_values() - 获取订单旧值
4. _handle_deduct_or_refund() - 扣款/退款处理

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
# 测试类1: _calculate_credit_level 信用等级计算函数测试
# =============================================================================

class TestCalculateCreditLevel:
    """
    测试 _calculate_credit_level 函数

    函数逻辑：
    - TotalSpent >= 10000 → 5级
    - TotalSpent >= 5000  → 4级
    - TotalSpent >= 2000  → 3级
    - TotalSpent >= 1000  → 2级
    - 否则               → 1级
    """

    # ------------------- 边界值测试 (Boundary Value Testing) -------------------

    @pytest.mark.unit
    @pytest.mark.boundary
    @pytest.mark.parametrize("totalspent,expected_level", [
        # 等级1边界
        (Decimal('0.00'), 1),          # 下边界：0
        (Decimal('0.01'), 1),          # 刚超过0
        (Decimal('999.99'), 1),        # 等级1上边界
        (Decimal('1000.00'), 2),       # 等级2下边界 ★边界值
        (Decimal('1000.01'), 2),       # 刚超过等级2下边界

        # 等级2边界
        (Decimal('1999.99'), 2),       # 等级2上边界
        (Decimal('2000.00'), 3),       # 等级3下边界 ★边界值
        (Decimal('2000.01'), 3),       # 刚超过等级3下边界

        # 等级3边界
        (Decimal('4999.99'), 3),        # 等级3上边界
        (Decimal('5000.00'), 4),       # 等级4下边界 ★边界值
        (Decimal('5000.01'), 4),       # 刚超过等级4下边界

        # 等级4边界
        (Decimal('9999.99'), 4),       # 等级4上边界
        (Decimal('10000.00'), 5),      # 等级5下边界 ★边界值
        (Decimal('10000.01'), 5),      # 刚超过等级5下边界

        # 等级5边界
        (Decimal('50000.00'), 5),      # 远超过等级5
        (Decimal('100000.00'), 5),     # 极端大值
    ])
    def test_boundary_values(self, totalspent, expected_level):
        """边界值测试：测试所有关键边界点"""
        from bookstore.signals import _calculate_credit_level
        result = _calculate_credit_level(totalspent)
        assert result == expected_level, f"TotalSpent={totalspent} 应返回等级{expected_level}，实际返回{result}"

    # ------------------- 等价类测试 (Equivalence Class Testing) -------------------

    @pytest.mark.unit
    @pytest.mark.equivalence
    @pytest.mark.parametrize("totalspent,expected_level,description", [
        (Decimal('500.00'), 1, "等级1代表值：普通新用户"),
        (Decimal('1500.00'), 2, "等级2代表值：活跃用户"),
        (Decimal('3500.00'), 3, "等级3代表值：资深用户"),
        (Decimal('7500.00'), 4, "等级4代表值：高级用户"),
        (Decimal('15000.00'), 5, "等级5代表值：VIP用户"),
    ])
    def test_equivalence_classes(self, totalspent, expected_level, description):
        """等价类测试：测试每个等价类的代表值"""
        from bookstore.signals import _calculate_credit_level
        result = _calculate_credit_level(totalspent)
        assert result == expected_level, f"{description}：TotalSpent={totalspent} 应返回等级{expected_level}"

    # ------------------- 独立路径测试 (Independent Path Testing) -------------------

    @pytest.mark.unit
    @pytest.mark.path
    def test_path_level_1(self):
        """独立路径1：TotalSpent < 1000 → 等级1"""
        from bookstore.signals import _calculate_credit_level
        assert _calculate_credit_level(Decimal('500')) == 1
        assert _calculate_credit_level(Decimal('0')) == 1
        assert _calculate_credit_level(Decimal('999.99')) == 1

    @pytest.mark.unit
    @pytest.mark.path
    def test_path_level_2(self):
        """独立路径2：1000 <= TotalSpent < 2000 → 等级2"""
        from bookstore.signals import _calculate_credit_level
        assert _calculate_credit_level(Decimal('1000')) == 2
        assert _calculate_credit_level(Decimal('1500')) == 2
        assert _calculate_credit_level(Decimal('1999.99')) == 2

    @pytest.mark.unit
    @pytest.mark.path
    def test_path_level_3(self):
        """独立路径3：2000 <= TotalSpent < 5000 → 等级3"""
        from bookstore.signals import _calculate_credit_level
        assert _calculate_credit_level(Decimal('2000')) == 3
        assert _calculate_credit_level(Decimal('3500')) == 3
        assert _calculate_credit_level(Decimal('4999.99')) == 3

    @pytest.mark.unit
    @pytest.mark.path
    def test_path_level_4(self):
        """独立路径4：5000 <= TotalSpent < 10000 → 等级4"""
        from bookstore.signals import _calculate_credit_level
        assert _calculate_credit_level(Decimal('5000')) == 4
        assert _calculate_credit_level(Decimal('7500')) == 4
        assert _calculate_credit_level(Decimal('9999.99')) == 4

    @pytest.mark.unit
    @pytest.mark.path
    def test_path_level_5(self):
        """独立路径5：TotalSpent >= 10000 → 等级5"""
        from bookstore.signals import _calculate_credit_level
        assert _calculate_credit_level(Decimal('10000')) == 5
        assert _calculate_credit_level(Decimal('50000')) == 5
        assert _calculate_credit_level(Decimal('1000000')) == 5

    # ------------------- 异常值测试 -------------------

    @pytest.mark.unit
    @pytest.mark.parametrize("totalspent,expected_level", [
        (None, 1),                     # None值应返回最低等级
        (Decimal('-100.00'), 1),       # 负数应返回最低等级
        (Decimal('0'), 1),             # 零值
    ])
    def test_edge_cases(self, totalspent, expected_level):
        """异常值测试：处理边界和异常输入"""
        from bookstore.signals import _calculate_credit_level
        result = _calculate_credit_level(totalspent)
        assert result == expected_level


# =============================================================================
# 测试类2: _get_old_order_values 订单旧值获取函数测试
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
            # 创建一个能够正确抛出ObjectDoesNotExist的mock类
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
# 测试类3: process_payment 支付处理函数测试
# =============================================================================

class TestProcessPayment:
    """
    测试 process_payment 函数

    支付场景：
    1. use_credit_only=True：纯信用支付
    2. use_credit_only=False + 余额充足：余额支付
    3. use_credit_only=False + 余额不足：余额+信用混合支付
    """

    def _create_mock_customer(self, balance=Decimal('1000.00'), creditlimit=Decimal('5000.00'),
                             usedcredit=Decimal('0.00'), totalspent=Decimal('500.00'),
                             canusecredit=1, levelid=2):
        """创建模拟客户对象"""
        customer = Mock()
        customer.balance = balance
        customer.creditlimit = creditlimit
        customer.usedcredit = usedcredit
        customer.totalspent = totalspent

        creditlevel = Mock()
        creditlevel.canusecredit = canusecredit
        creditlevel.levelid = levelid
        customer.levelid = creditlevel

        return customer

    def _create_mock_order(self, totalamount=Decimal('100.00')):
        """创建模拟订单对象"""
        order = Mock()
        order.totalamount = totalamount
        return order

    # ------------------- 场景法测试 (Scenario Testing) -------------------

    @pytest.mark.unit
    @pytest.mark.scenario
    @pytest.mark.payment
    def test_scenario_credit_only_success(self):
        """场景1：纯信用支付成功"""
        from bookstore.signals import process_payment

        customer = self._create_mock_customer(
            balance=Decimal('100.00'),
            creditlimit=Decimal('5000.00'),
            usedcredit=Decimal('0.00'),
            canusecredit=1
        )
        order = self._create_mock_order(totalamount=Decimal('200.00'))

        with patch('bookstore.signals.Creditlevel') as mock_creditlevel, \
             patch('bookstore.signals.transaction.atomic', return_value=mock_transaction_atomic()):
            mock_credit_obj = Mock()
            mock_credit_obj.levelid = 2
            mock_creditlevel.objects.get.return_value = mock_credit_obj

            success, result = process_payment(order, customer, use_credit_only=True)

        assert success is True
        assert '信用支付成功' in result[0]
        assert customer.usedcredit == Decimal('200.00')
        assert customer.balance == Decimal('100.00')  # 余额不变

    @pytest.mark.unit
    @pytest.mark.scenario
    @pytest.mark.payment
    def test_scenario_credit_only_insufficient_limit(self):
        """场景2：纯信用支付 - 信用额度不足"""
        from bookstore.signals import process_payment

        customer = self._create_mock_customer(
            balance=Decimal('0.00'),
            creditlimit=Decimal('100.00'),
            usedcredit=Decimal('50.00'),
            canusecredit=1
        )
        order = self._create_mock_order(totalamount=Decimal('100.00'))

        success, msg = process_payment(order, customer, use_credit_only=True)

        assert success is False
        assert '信用额度不足' in msg or '可用额度' in msg
        assert customer.usedcredit == Decimal('50.00')  # 未改变

    @pytest.mark.unit
    @pytest.mark.scenario
    @pytest.mark.payment
    def test_scenario_credit_only_cannot_use_credit(self):
        """场景3：纯信用支付 - 该等级不支持信用支付"""
        from bookstore.signals import process_payment

        customer = self._create_mock_customer(
            balance=Decimal('0.00'),
            canusecredit=0,  # 不支持信用支付
            levelid=1
        )
        order = self._create_mock_order(totalamount=Decimal('100.00'))

        success, msg = process_payment(order, customer, use_credit_only=True)

        assert success is False
        assert '不支持信用支付' in msg

    @pytest.mark.unit
    @pytest.mark.scenario
    @pytest.mark.payment
    def test_scenario_balance_sufficient(self):
        """场景4：余额支付 - 余额充足"""
        from bookstore.signals import process_payment

        customer = self._create_mock_customer(
            balance=Decimal('500.00'),
            totalspent=Decimal('100.00')
        )
        order = self._create_mock_order(totalamount=Decimal('200.00'))

        with patch('bookstore.signals.Creditlevel') as mock_creditlevel, \
             patch('bookstore.signals.transaction.atomic', return_value=mock_transaction_atomic()):
            mock_credit_obj = Mock()
            mock_credit_obj.levelid = 2
            mock_creditlevel.objects.get.return_value = mock_credit_obj

            success, result = process_payment(order, customer, use_credit_only=False)

        assert success is True
        assert '支付成功' in result[0]
        assert customer.balance == Decimal('300.00')  # 500 - 200
        assert customer.totalspent == Decimal('300.00')  # 100 + 200

    @pytest.mark.unit
    @pytest.mark.scenario
    @pytest.mark.payment
    def test_scenario_balance_insufficient_with_credit(self):
        """场景5：余额+信用混合支付 - 余额不足但信用充足"""
        from bookstore.signals import process_payment

        customer = self._create_mock_customer(
            balance=Decimal('50.00'),
            creditlimit=Decimal('5000.00'),
            usedcredit=Decimal('0.00'),
            totalspent=Decimal('100.00')
        )
        order = self._create_mock_order(totalamount=Decimal('200.00'))

        with patch('bookstore.signals.Creditlevel') as mock_creditlevel, \
             patch('bookstore.signals.transaction.atomic', return_value=mock_transaction_atomic()):
            mock_credit_obj = Mock()
            mock_credit_obj.levelid = 2
            mock_creditlevel.objects.get.return_value = mock_credit_obj

            success, result = process_payment(order, customer, use_credit_only=False)

        assert success is True
        assert customer.balance == Decimal('0.00')
        assert customer.usedcredit == Decimal('150.00')  # 200 - 50
        assert customer.totalspent == Decimal('150.00')  # 100 + 50

    @pytest.mark.unit
    @pytest.mark.scenario
    @pytest.mark.payment
    def test_scenario_balance_insufficient_credit_insufficient(self):
        """场景6：余额+信用混合支付 - 信用额度也不足"""
        from bookstore.signals import process_payment

        customer = self._create_mock_customer(
            balance=Decimal('50.00'),
            creditlimit=Decimal('100.00'),
            usedcredit=Decimal('80.00'),  # 已用80，可用20
            totalspent=Decimal('100.00')
        )
        order = self._create_mock_order(totalamount=Decimal('200.00'))  # 需要150

        with patch('bookstore.signals.Creditlevel') as mock_creditlevel, \
             patch('bookstore.signals.transaction.atomic', return_value=mock_transaction_atomic()):
            mock_credit_obj = Mock()
            mock_credit_obj.levelid = 2
            mock_creditlevel.objects.get.return_value = mock_credit_obj

            success, msg = process_payment(order, customer, use_credit_only=False)

        assert success is False
        assert '信用' in msg or '充值' in msg
        assert customer.balance == Decimal('50.00')  # 未改变
        assert customer.usedcredit == Decimal('80.00')  # 未改变

    @pytest.mark.unit
    @pytest.mark.scenario
    @pytest.mark.payment
    def test_scenario_balance_insufficient_cannot_use_credit(self):
        """场景7：余额+信用混合支付 - 余额不足且不支持信用"""
        from bookstore.signals import process_payment

        customer = self._create_mock_customer(
            balance=Decimal('50.00'),
            canusecredit=0,
            levelid=1
        )
        order = self._create_mock_order(totalamount=Decimal('200.00'))

        success, msg = process_payment(order, customer, use_credit_only=False)

        assert success is False
        assert '不支持信用支付' in msg

    # ------------------- 边界值测试 (Boundary Value Testing) -------------------

    @pytest.mark.unit
    @pytest.mark.boundary
    @pytest.mark.payment
    @pytest.mark.parametrize("balance,amount,expected_balance", [
        # 金额边界
        (Decimal('100.00'), Decimal('0.00'), Decimal('100.00')),  # 零金额订单
        (Decimal('100.00'), Decimal('0.01'), Decimal('99.99')),   # 最小正金额
        (Decimal('100.00'), Decimal('100.00'), Decimal('0.00')), # 刚好用完余额
    ])
    def test_boundary_value_payment(self, balance, amount, expected_balance):
        """边界值测试：支付金额边界"""
        from bookstore.signals import process_payment

        customer = self._create_mock_customer(balance=balance)
        order = self._create_mock_order(totalamount=amount)

        with patch('bookstore.signals.Creditlevel') as mock_creditlevel, \
             patch('bookstore.signals.transaction.atomic', return_value=mock_transaction_atomic()):
            mock_credit_obj = Mock()
            mock_credit_obj.levelid = 2
            mock_creditlevel.objects.get.return_value = mock_credit_obj

            if amount > Decimal('0'):
                success, result = process_payment(order, customer, use_credit_only=False)
                assert success is True
                assert customer.balance == expected_balance

    @pytest.mark.unit
    @pytest.mark.boundary
    @pytest.mark.credit
    @pytest.mark.parametrize("totalspent,expected_level", [
        (Decimal('999.99'), 1),        # 升级边界下
        (Decimal('1000.00'), 2),       # 升级边界点
    ])
    def test_credit_level_upgrade_boundary(self, totalspent, expected_level):
        """边界值测试：信用等级升级边界"""
        from bookstore.signals import process_payment

        customer = self._create_mock_customer(
            balance=Decimal('10000.00'),
            totalspent=totalspent
        )
        order = self._create_mock_order(totalamount=Decimal('100.00'))

        with patch('bookstore.signals.Creditlevel') as mock_creditlevel, \
             patch('bookstore.signals.transaction.atomic', return_value=mock_transaction_atomic()):
            mock_credit_obj = Mock()
            mock_credit_obj.levelid = expected_level
            mock_creditlevel.objects.get.return_value = mock_credit_obj

            success, result = process_payment(order, customer, use_credit_only=False)
            assert success is True


# =============================================================================
# 测试类4: _handle_deduct_or_refund 扣款/退款处理函数测试
# =============================================================================

class TestHandleDeductOrRefund:
    """
    测试 _handle_deduct_or_refund 函数

    订单状态流转：
    - status=0: 待付款
    - status=1: 已付款/处理中
    - status=2: 已完成
    - status=3: 已取消(退款)
    - status=4: 取消中/已取消

    测试场景：
    1. 订单取消(status=4)：触发退款逻辑
    2. 订单完成(status=2)：不额外处理
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

    def _create_mock_customer(self, balance=Decimal('1000.00'),
                             usedcredit=Decimal('0.00'),
                             totalspent=Decimal('500.00'),
                             levelid=2):
        """创建模拟客户"""
        customer = Mock()
        customer.balance = balance
        customer.usedcredit = usedcredit
        customer.totalspent = totalspent
        customer.levelid = Mock()
        customer.levelid.levelid = levelid
        return customer

    # ------------------- 场景法测试 (Scenario Testing) -------------------

    @pytest.mark.unit
    @pytest.mark.scenario
    def test_scenario_order_cancel_refund_balance(self):
        """场景1：订单取消 - 退还余额支付部分"""
        from bookstore.signals import _handle_deduct_or_refund

        instance = self._create_mock_instance(
            status=4,  # 取消
            totalamount=Decimal('200.00'),
            actualpaid=Decimal('200.00'),  # 已全额付款
            paymentstatus=1  # 已付款
        )
        old_status = 0  # 原状态为待付款

        mock_customer = self._create_mock_customer(
            balance=Decimal('100.00'),
            totalspent=Decimal('700.00')  # 原有消费
        )

        with patch('bookstore.signals.Customer') as mock_customer_class, \
             patch('bookstore.signals._calculate_credit_level', return_value=1), \
             patch('bookstore.signals.Creditlevel') as mock_creditlevel, \
             patch('bookstore.signals.transaction.atomic', return_value=mock_transaction_atomic()):
            mock_customer_class.objects.select_for_update.return_value.select_related.return_value.get.return_value = mock_customer
            mock_credit_obj = Mock()
            mock_credit_obj.levelid = 1
            mock_creditlevel.objects.get.return_value = mock_credit_obj

            _handle_deduct_or_refund(instance, old_status, Decimal('200.00'))

        assert mock_customer.balance == Decimal('300.00')  # 100 + 200
        assert mock_customer.totalspent == Decimal('500.00')  # 700 - 200

    @pytest.mark.unit
    @pytest.mark.scenario
    def test_scenario_order_cancel_refund_credit(self):
        """场景2：订单取消 - 释放信用额度"""
        from bookstore.signals import _handle_deduct_or_refund

        instance = self._create_mock_instance(
            status=4,  # 取消
            totalamount=Decimal('200.00'),
            actualpaid=Decimal('50.00'),  # 实际付款50
            paymentstatus=2  # 使用信用
        )
        old_status = 0

        mock_customer = self._create_mock_customer(
            balance=Decimal('0.00'),
            usedcredit=Decimal('150.00'),
            totalspent=Decimal('50.00')
        )

        with patch('bookstore.signals.Customer') as mock_customer_class, \
             patch('bookstore.signals._calculate_credit_level', return_value=1), \
             patch('bookstore.signals.Creditlevel') as mock_creditlevel, \
             patch('bookstore.signals.transaction.atomic', return_value=mock_transaction_atomic()):
            mock_customer_class.objects.select_for_update.return_value.select_related.return_value.get.return_value = mock_customer
            mock_credit_obj = Mock()
            mock_credit_obj.levelid = 1
            mock_creditlevel.objects.get.return_value = mock_credit_obj

            _handle_deduct_or_refund(instance, old_status, Decimal('200.00'))

        assert mock_customer.usedcredit == Decimal('0.00')  # 释放信用
        assert instance.paymentstatus == 3  # 退款状态

    @pytest.mark.unit
    @pytest.mark.scenario
    def test_scenario_order_complete(self):
        """场景3：订单完成 - 不额外处理TotalSpent"""
        from bookstore.signals import _handle_deduct_or_refund

        instance = self._create_mock_instance(status=2)
        old_status = 1  # 原状态为已付款

        mock_customer = self._create_mock_customer(totalspent=Decimal('500.00'))

        with patch('bookstore.signals.Customer') as mock_customer_class, \
             patch('bookstore.signals.transaction.atomic', return_value=mock_transaction_atomic()):
            mock_customer_class.objects.select_for_update.return_value.select_related.return_value.get.return_value = mock_customer

            original_totalspent = mock_customer.totalspent

            _handle_deduct_or_refund(instance, old_status, Decimal('100.00'))

            assert mock_customer.totalspent == original_totalspent  # 不变

    @pytest.mark.unit
    @pytest.mark.scenario
    def test_scenario_status_unchanged(self):
        """场景4：状态未变化 - 不处理"""
        from bookstore.signals import _handle_deduct_or_refund

        instance = self._create_mock_instance(status=0)
        old_status = 0  # 状态未变

        mock_customer = self._create_mock_customer()

        with patch('bookstore.signals.Customer') as mock_customer_class, \
             patch('bookstore.signals.transaction.atomic', return_value=mock_transaction_atomic()):
            mock_customer_class.objects.select_for_update.return_value.select_related.return_value.get.return_value = mock_customer

            original_balance = mock_customer.balance

            _handle_deduct_or_refund(instance, old_status, Decimal('100.00'))

            assert mock_customer.balance == original_balance  # 不变

    # ------------------- 边界值测试 (Boundary Value Testing) -------------------

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

        mock_customer = self._create_mock_customer(totalspent=Decimal('0.00'))

        with patch('bookstore.signals.Customer') as mock_customer_class, \
             patch('bookstore.signals._calculate_credit_level', return_value=1), \
             patch('bookstore.signals.Creditlevel') as mock_creditlevel, \
             patch('bookstore.signals.transaction.atomic', return_value=mock_transaction_atomic()):
            mock_customer_class.objects.select_for_update.return_value.select_related.return_value.get.return_value = mock_customer
            mock_credit_obj = Mock()
            mock_credit_obj.levelid = 1
            mock_creditlevel.objects.get.return_value = mock_credit_obj

            _handle_deduct_or_refund(instance, old_status, Decimal('0.00'))

        assert mock_customer.totalspent == Decimal('0.00')

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

        mock_customer = self._create_mock_customer(
            balance=Decimal('0.00'),
            totalspent=Decimal('10000.00'),
            levelid=5  # 高级别
        )

        with patch('bookstore.signals.Customer') as mock_customer_class, \
             patch('bookstore.signals._calculate_credit_level', return_value=1), \
             patch('bookstore.signals.Creditlevel') as mock_creditlevel, \
             patch('bookstore.signals.transaction.atomic', return_value=mock_transaction_atomic()):
            mock_customer_class.objects.select_for_update.return_value.select_related.return_value.get.return_value = mock_customer
            mock_credit_obj = Mock()
            mock_credit_obj.levelid = 1
            mock_creditlevel.objects.get.return_value = mock_credit_obj

            _handle_deduct_or_refund(instance, old_status, Decimal('10000.00'))

        assert mock_customer.balance == Decimal('10000.00')
        assert mock_customer.totalspent == Decimal('0.00')

    # ------------------- 独立路径测试 (Independent Path Testing) -------------------

    @pytest.mark.unit
    @pytest.mark.path
    def test_path_cancel_with_balance_payment(self):
        """独立路径：取消 + 有余额支付"""
        from bookstore.signals import _handle_deduct_or_refund

        instance = self._create_mock_instance(status=4, actualpaid=Decimal('100.00'))
        mock_customer = self._create_mock_customer(balance=Decimal('200.00'), totalspent=Decimal('100.00'))

        with patch('bookstore.signals.Customer') as mock_customer_class, \
             patch('bookstore.signals._calculate_credit_level', return_value=1), \
             patch('bookstore.signals.Creditlevel') as mock_creditlevel, \
             patch('bookstore.signals.transaction.atomic', return_value=mock_transaction_atomic()):
            mock_customer_class.objects.select_for_update.return_value.select_related.return_value.get.return_value = mock_customer
            mock_credit_obj = Mock()
            mock_credit_obj.levelid = 1
            mock_creditlevel.objects.get.return_value = mock_credit_obj

            _handle_deduct_or_refund(instance, 0, Decimal('100.00'))

        assert mock_customer.balance == Decimal('300.00')

    @pytest.mark.unit
    @pytest.mark.path
    def test_path_cancel_with_credit_used(self):
        """独立路径：取消 + 使用了信用"""
        from bookstore.signals import _handle_deduct_or_refund

        instance = self._create_mock_instance(
            status=4, totalamount=Decimal('200.00'),
            actualpaid=Decimal('50.00'), paymentstatus=2
        )
        mock_customer = self._create_mock_customer(usedcredit=Decimal('150.00'))

        with patch('bookstore.signals.Customer') as mock_customer_class, \
             patch('bookstore.signals._calculate_credit_level', return_value=1), \
             patch('bookstore.signals.Creditlevel') as mock_creditlevel, \
             patch('bookstore.signals.transaction.atomic', return_value=mock_transaction_atomic()):
            mock_customer_class.objects.select_for_update.return_value.select_related.return_value.get.return_value = mock_customer
            mock_credit_obj = Mock()
            mock_credit_obj.levelid = 1
            mock_creditlevel.objects.get.return_value = mock_credit_obj

            _handle_deduct_or_refund(instance, 0, Decimal('200.00'))

        assert mock_customer.usedcredit == Decimal('0.00')

    @pytest.mark.unit
    @pytest.mark.path
    def test_path_complete_no_action(self):
        """独立路径：完成订单无操作"""
        from bookstore.signals import _handle_deduct_or_refund

        instance = self._create_mock_instance(status=2)
        mock_customer = self._create_mock_customer(totalspent=Decimal('1000.00'))

        with patch('bookstore.signals.Customer') as mock_customer_class, \
             patch('bookstore.signals.transaction.atomic', return_value=mock_transaction_atomic()):
            mock_customer_class.objects.select_for_update.return_value.select_related.return_value.get.return_value = mock_customer

            original = mock_customer.totalspent
            _handle_deduct_or_refund(instance, 1, Decimal('100.00'))

            assert mock_customer.totalspent == original


# =============================================================================
# 测试类5: 集成测试 - 支付流程完整测试
# =============================================================================

class TestPaymentIntegration:
    """
    集成测试：完整的支付和退款流程

    测试完整的业务流程：
    1. 用户下单 → 创建订单
    2. 用户支付 → 扣款/更新信用
    3. 订单完成 → 更新状态
    4. 订单取消 → 退款
    """

    @pytest.mark.integration
    @pytest.mark.payment
    def test_cancel_and_refund_flow(self):
        """完整流程测试：下单→支付→取消→退款"""
        from bookstore.signals import _handle_deduct_or_refund

        customer = Mock()
        customer.balance = Decimal('200.00')
        customer.totalspent = Decimal('300.00')
        customer.usedcredit = Decimal('0.00')
        customer.levelid = Mock()
        customer.levelid.levelid = 2

        with patch('bookstore.signals.Customer') as mock_customer_class, \
             patch('bookstore.signals._calculate_credit_level', return_value=1), \
             patch('bookstore.signals.Creditlevel') as mock_creditlevel, \
             patch('bookstore.signals.transaction.atomic', return_value=mock_transaction_atomic()):
            mock_customer_class.objects.select_for_update.return_value.select_related.return_value.get.return_value = customer
            mock_credit_obj = Mock()
            mock_credit_obj.levelid = 1
            mock_creditlevel.objects.get.return_value = mock_credit_obj

            # 1. 创建订单并支付
            order = Mock()
            order.orderid = 1
            order.totalamount = Decimal('300.00')
            order.actualpaid = Decimal('300.00')
            order.paymentstatus = 1

            # 2. 取消订单
            order.status = 4
            _handle_deduct_or_refund(order, 1, Decimal('300.00'))

        assert customer.balance == Decimal('500.00')  # 200 + 300
        assert customer.totalspent == Decimal('0.00')  # 300 - 300


# =============================================================================
# 测试报告辅助函数
# =============================================================================

def get_test_summary():
    """生成测试摘要信息"""
    return {
        'total_functions': 4,
        'total_test_classes': 5,
        'functions_tested': [
            '_calculate_credit_level',
            'process_payment',
            '_get_old_order_values',
            '_handle_deduct_or_refund'
        ],
        'test_methods': [
            'boundary', 'equivalence', 'scenario', 'path', 'integration'
        ]
    }
