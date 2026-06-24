import pytest
from decimal import Decimal
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from django.db import connection
from bookstore.models import Customer, Creditlevel

# ===================== pytest-django 配置 =====================

@pytest.fixture(scope='session', autouse=True)
def create_tables(django_db_setup, django_db_blocker):
    """测试会话开始时创建无管理的测试表结构"""
    with django_db_blocker.unblock():
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS customer")
            cursor.execute("DROP TABLE IF EXISTS creditlevel")
            
            cursor.execute("""
            CREATE TABLE creditlevel (
                LevelID INTEGER PRIMARY KEY,
                DiscountRate DECIMAL(3,2),
                CanUseCredit INTEGER,
                CreditLimit DECIMAL(10,2)
            )
            """)
            cursor.execute("""
            CREATE TABLE customer (
                CustomerID INTEGER PRIMARY KEY AUTOINCREMENT,
                Username VARCHAR(50) UNIQUE,
                Password VARCHAR(50),
                Name VARCHAR(50),
                Address VARCHAR(200),
                Email VARCHAR(100) UNIQUE,
                Balance DECIMAL(10,2),
                LevelID INTEGER,
                CreditLimit DECIMAL(10,2),
                UsedCredit DECIMAL(10,2),
                TotalSpent DECIMAL(12,2),
                RegisterDate DATETIME,
                FOREIGN KEY (LevelID) REFERENCES creditlevel(LevelID)
            )
            """)
    yield

# ===================== 测试工具与Fixture =====================

def make_request_with_messages(factory, method, path, data=None, session_data=None):
    """创建带有 messages 和 session 的 Request 对象"""
    request = factory.get(path) if method == 'GET' else factory.post(path, data or {})
    request.session = session_data or {}
    messages = FallbackStorage(request)
    request._messages = messages
    return request

@pytest.fixture
def factory():
    return RequestFactory()

@pytest.fixture
def credit_level_1(db):
    """为新注册用户提供默认的等级1数据"""
    return Creditlevel.objects.create(
        levelid=1, discountrate=Decimal('1.00'), canusecredit=0, creditlimit=Decimal('0.00')
    )

@pytest.fixture
def test_customer(db, credit_level_1):
    """创建并返回一个供测试登录的已有客户"""
    from django.utils import timezone
    return Customer.objects.create(
        username='testuser', password='password123', name='测试用户',
        email='test@example.com', address='地址', balance=Decimal('0.00'),
        levelid=credit_level_1, creditlimit=Decimal('0.00'),
        usedcredit=Decimal('0.00'), totalspent=Decimal('0.00'), registerdate=timezone.now()
    )

# ===================== 登录模块测试 (customer_login) =====================

@pytest.mark.django_db
class TestCustomerLogin:
    def test_get_request_returns_login_page(self, factory):
        """场景：GET 访问登录页面应该正常返回 200 HTML"""
        from bookstore.views import customer_login
        req = make_request_with_messages(factory, 'GET', '/login/')
        resp = customer_login(req)
        assert resp.status_code == 200

    def test_login_success(self, factory, test_customer):
        """等价类（有效）：输入正确的账号密码"""
        from bookstore.views import customer_login
        req = make_request_with_messages(factory, 'POST', '/login/', {'username': 'testuser', 'password': 'password123'})
        resp = customer_login(req)
        assert resp.status_code == 302
        assert req.session.get('customer_id') == test_customer.customerid

    def test_login_wrong_pwd_or_user(self, factory, test_customer):
        """等价类（无效）：密码错误 或 用户不存在"""
        from bookstore.views import customer_login
        # 密码错误
        req1 = make_request_with_messages(factory, 'POST', '/login/', {'username': 'testuser', 'password': 'err'})
        assert customer_login(req1).status_code == 200
        # 用户不存在
        req2 = make_request_with_messages(factory, 'POST', '/login/', {'username': 'none', 'password': '123'})
        assert customer_login(req2).status_code == 200

# ===================== 注册模块测试 (customer_register) =====================

@pytest.mark.django_db
class TestCustomerRegister:
    def test_register_success(self, factory, db, credit_level_1):
        """等价类（有效）：完善的信息注册，测试成功重定向 (依赖 credit_level_1)"""
        from bookstore.views import customer_register
        req = make_request_with_messages(factory, 'POST', '/register/', {
            'username': 'newuser', 'password': 'password123', 'confirm_password': 'password123',
            'name': '新用户', 'email': 'new@test.com'
        })
        resp = customer_register(req)
        assert resp.status_code == 302
        assert Customer.objects.filter(username='newuser').exists()
        assert req.session.get("customer_name") == "新用户"

    def test_register_missing_fields(self, factory):
        """等价类（无效）：缺少必填字段"""
        from bookstore.views import customer_register
        req = make_request_with_messages(factory, 'POST', '/register/', {'username': 'newuser'})
        assert customer_register(req).status_code == 200
        assert not Customer.objects.filter(username='newuser').exists()

    def test_register_password_boundary(self, factory, db, credit_level_1):
        """边界值：密码长度测试"""
        from bookstore.views import customer_register
        # 小于 6位 （无效边界）
        req_invalid = make_request_with_messages(factory, 'POST', '/register/', {
            'username': 'usr1', 'password': '123', 'confirm_password': '123', 'name': 'A', 'email': 'a@a.com'
        })
        assert customer_register(req_invalid).status_code == 200

        # 正好 6位 （有效边界）
        req_valid = make_request_with_messages(factory, 'POST', '/register/', {
            'username': 'usr6', 'password': '123456', 'confirm_password': '123456', 'name': 'B', 'email': 'b@b.com'
        })
        customer_register(req_valid)
        assert Customer.objects.filter(username='usr6').exists()

    def test_password_mismatch(self, factory, credit_level_1):
        """等价类（无效）：两次密码不一致"""
        from bookstore.views import customer_register
        req = make_request_with_messages(factory, 'POST', '/register/', {
            'username': 'u', 'password': '123456', 'confirm_password': '1234567', 'name': 'A', 'email': 'u@a.com'
        })
        assert customer_register(req).status_code == 200

    def test_register_duplicate(self, factory, test_customer, credit_level_1):
        """等价类（无效）：用户名重名或邮箱被占用"""
        from bookstore.views import customer_register
        # 用户名重复
        req_dup_user = make_request_with_messages(factory, 'POST', '/register/', {
            'username': 'testuser', 'password': 'pwd', 'confirm_password': 'pwd', 'name': 'A', 'email': '1@a.com'
        })
        assert customer_register(req_dup_user).status_code == 200
        # 邮箱重复
        req_dup_mail = make_request_with_messages(factory, 'POST', '/register/', {
            'username': 'new2', 'password': 'pwd', 'confirm_password': 'pwd', 'name': 'A', 'email': 'test@example.com'
        })
        assert customer_register(req_dup_mail).status_code == 200

# ===================== 登出及拦截器测试 =====================

@pytest.mark.django_db
class TestLogoutAndDecorators:
    def test_customer_logout(self, factory):
        """测试登出清理 Session 功能"""
        from bookstore.views import customer_logout
        req = make_request_with_messages(factory, 'POST', '/logout/', session_data={'customer_id': 1, 'customer_name': 'Test'})
        resp = customer_logout(req)
        assert resp.status_code == 302
        assert 'customer_id' not in req.session
        assert 'customer_name' not in req.session

    def test_customer_required_decorator(self, factory):
        """测试拦截器针对未登录状态的跳转"""
        from bookstore.views import customer_required
        from django.http import HttpResponse
        
        @customer_required
        def dummy_view(request):
            return HttpResponse("OK")
            
        req = make_request_with_messages(factory, 'GET', '/dummy/', session_data={})
        resp = dummy_view(req)
        assert resp.status_code == 302  # 被定向到登录页

# ===================== 账户充值模块测试 (account_recharge) =====================

@pytest.mark.django_db
class TestAccountRecharge:
    def test_recharge_success(self, factory, test_customer):
        """等价类（有效）：输入合法的金额执行充值"""
        from bookstore.views import account_wallet as account_recharge
        from decimal import Decimal
        request = make_request_with_messages(factory, 'POST', '/account/', {'amount': '100.00'}, session_data={
            'customer_id': test_customer.customerid,
            'customer_name': test_customer.name
        })
        response = account_recharge(request)
        test_customer.refresh_from_db()  # 必须从数据库重新读取以验证
        assert test_customer.balance == Decimal('100.00')  # 测试初始为0，充值100必定为100
        assert response.status_code == 302  # 成功应该重定向

    def test_recharge_invalid_amount(self, factory, test_customer):
        """等价类（无效）：输入的金额包含负数或非法字母"""
        from bookstore.views import account_wallet as account_recharge
        from decimal import Decimal
        # 场景1：输入金额为负数
        req_negative = make_request_with_messages(factory, 'POST', '/account/', {'amount': '-50'}, session_data={
            'customer_id': test_customer.customerid
        })
        assert account_recharge(req_negative).status_code == 200  # 解析失败不跳转，停留在原页面展示错误信息

        # 场景2：输入杂串字母
        req_letter = make_request_with_messages(factory, 'POST', '/account/', {'amount': 'abc'}, session_data={
            'customer_id': test_customer.customerid
        })
        assert account_recharge(req_letter).status_code == 200


# ===================== 账户信息编辑测试 (account_edit) =====================

@pytest.mark.django_db
class TestAccountEdit:
    def test_edit_basic_info_success(self, factory, test_customer):
        """等价类（有效）：仅修改用户的基本信息（姓名、邮箱）"""
        from bookstore.views import account_edit
        request = make_request_with_messages(factory, 'POST', '/account/edit/', {
            'name': '马里奥',
            'email': 'mario@example.com',
            'address': '蘑菇王国',
            'current_password': '',
            'new_password': '',
            'confirm_password': ''
        }, session_data={
            'customer_id': test_customer.customerid,
            'customer_name': test_customer.name
        })
        response = account_edit(request)
        test_customer.refresh_from_db()
        assert test_customer.name == '马里奥'
        assert test_customer.email == 'mario@example.com'
        assert response.status_code == 302

    def test_edit_duplicate_email(self, factory, test_customer, credit_level_1):
        """等价类（无效）：尝试修改为一个已被其他人注册占用的邮箱"""
        from bookstore.models import Customer
        from django.utils import timezone
        from decimal import Decimal
        # 预先往数据库垫入"另一个用户"
        Customer.objects.create(
            username='other_user', password='123', name='路人甲', email='already@example.com',
            balance=Decimal('0.00'), levelid=credit_level_1, creditlimit=Decimal('0'),
            usedcredit=Decimal('0.00'), totalspent=Decimal('0.00'), registerdate=timezone.now()
        )
        
        from bookstore.views import account_edit
        request = make_request_with_messages(factory, 'POST', '/account/edit/', {
            'name': '用户', 'email': 'already@example.com'
        }, session_data={'customer_id': test_customer.customerid})
        
        response = account_edit(request)
        assert response.status_code == 302
        test_customer.refresh_from_db()
        assert test_customer.email != 'already@example.com'  # 核心断言：本用户的邮箱决不能被成功修改为已占用的那个

    def test_edit_password_success(self, factory, test_customer):
        """等价类（有效）：正确输入当前密码并设置合法的新密码"""
        from bookstore.views import account_edit
        request = make_request_with_messages(factory, 'POST', '/account/edit/', {
            'name': test_customer.name,
            'email': test_customer.email,
            'current_password': 'password123',  # 原密码
            'new_password': 'newpass123',       # 新密码
            'confirm_password': 'newpass123'
        }, session_data={'customer_id': test_customer.customerid})
        
        response = account_edit(request)
        test_customer.refresh_from_db()
        assert test_customer.password == 'newpass123'
