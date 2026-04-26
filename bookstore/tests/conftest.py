"""
Pytest配置文件 - 提供Django测试环境配置和共享fixture
"""
import os
import sys
import django
from decimal import Decimal

import pytest

# 确保Django设置在导入任何Django模块之前配置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MyBookwise.settings')

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@pytest.fixture(scope='session')
def django_db_setup():
    """配置Django测试数据库"""
    from django.conf import settings
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }


@pytest.fixture
def mock_customer_data():
    """提供模拟客户数据"""
    return {
        'customerid': 1,
        'username': 'testuser',
        'password': 'testpass123',
        'name': '测试用户',
        'address': '测试地址',
        'email': 'test@example.com',
        'balance': Decimal('1000.00'),
        'creditlimit': Decimal('5000.00'),
        'usedcredit': Decimal('0.00'),
        'totalspent': Decimal('500.00'),
    }


@pytest.fixture
def mock_order_data():
    """提供模拟订单数据"""
    return {
        'orderid': 1,
        'orderno': 'ORD-20250101-0001',
        'totalamount': Decimal('200.00'),
        'actualpaid': Decimal('0.00'),
        'paymentstatus': 0,
        'status': 0,
    }


@pytest.fixture
def mock_creditlevel_data():
    """提供模拟信用等级数据"""
    return {
        1: {'discountrate': Decimal('1.00'), 'canusecredit': 0, 'creditlimit': Decimal('0.00')},
        2: {'discountrate': Decimal('0.98'), 'canusecredit': 1, 'creditlimit': Decimal('1000.00')},
        3: {'discountrate': Decimal('0.95'), 'canusecredit': 1, 'creditlimit': Decimal('3000.00')},
        4: {'discountrate': Decimal('0.90'), 'canusecredit': 1, 'creditlimit': Decimal('5000.00')},
        5: {'discountrate': Decimal('0.85'), 'canusecredit': 1, 'creditlimit': Decimal('10000.00')},
    }


@pytest.fixture
def payment_amounts():
    """提供支付测试的边界值金额"""
    return {
        'zero': Decimal('0.00'),
        'min_positive': Decimal('0.01'),
        'boundary_small': Decimal('99.99'),
        'boundary_medium': Decimal('100.00'),
        'boundary_large': Decimal('999.99'),
        'boundary_xl': Decimal('1000.00'),
        'max': Decimal('10000.00'),
    }


@pytest.fixture
def balance_amounts():
    """提供余额测试的边界值"""
    return {
        'zero': Decimal('0.00'),
        'min_positive': Decimal('0.01'),
        'exactly_equal': Decimal('100.00'),
        'just_over': Decimal('100.01'),
        'much_less': Decimal('50.00'),
        'much_more': Decimal('5000.00'),
    }
