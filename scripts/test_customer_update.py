"""
测试客户余额和累计消费更新功能

使用方法:
    python scripts/test_customer_update.py
    
或在Django shell中:
    python manage.py shell
    >>> exec(open('scripts/test_customer_update.py').read())
"""

import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MyBookwise.settings')
django.setup()

from bookstore.models import Customer, Orders, Orderdetail
from decimal import Decimal


def print_separator(title=""):
    """打印分隔线"""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
    else:
        print(f"{'-'*60}")


def show_customer_info(customer_id):
    """显示客户详细信息"""
    try:
        customer = Customer.objects.get(pk=customer_id)
        print(f"客户ID: {customer.customerid}")
        print(f"用户名: {customer.username} ({customer.name})")
        print(f"余额: ¥{customer.balance}")
        print(f"累计消费: ¥{customer.totalspent}")
        print(f"信用等级: {customer.levelid.levelid}级 (折扣率: {customer.levelid.discountrate})")
        print(f"透支额度: ¥{customer.overdraftlimit}")
        return customer
    except Customer.DoesNotExist:
        print(f"❌ 客户ID {customer_id} 不存在")
        return None


def show_order_info(order_id):
    """显示订单详细信息"""
    try:
        order = Orders.objects.get(pk=order_id)
        details = Orderdetail.objects.filter(orderid=order)
        
        print(f"\n订单号: {order.orderno}")
        print(f"订单ID: {order.orderid}")
        print(f"客户: {order.customerid.name} (ID:{order.customerid.customerid})")
        print(f"下单时间: {order.orderdate}")
        print(f"总金额: ¥{order.totalamount}")
        print(f"状态: {get_status_name(order.status)}")
        
        print("\n订单明细:")
        for detail in details:
            shipped = "✓已发货" if detail.isshipped else "✗未发货"
            print(f"  - {detail.isbn.title} × {detail.quantity}本 @ ¥{detail.unitprice} [{shipped}]")
        
        return order
    except Orders.DoesNotExist:
        print(f"❌ 订单ID {order_id} 不存在")
        return None


def get_status_name(status):
    """获取订单状态名称"""
    status_map = {
        0: "已下单",
        1: "已发货",
        2: "已完成",
        3: "处理中",
        4: "已取消"
    }
    return f"{status} ({status_map.get(status, '未知')})"


def test_order_completion():
    """测试订单完成功能"""
    print_separator("测试1: 订单完成后更新TotalSpent")
    
    # 选择一个status=0的订单测试
    order = Orders.objects.filter(status=0).first()
    if not order:
        print("❌ 没有找到status=0的订单用于测试")
        return
    
    customer = order.customerid
    print("\n【修改前】")
    print(f"订单ID: {order.orderid}, 金额: ¥{order.totalamount}")
    show_customer_info(customer.customerid)
    
    old_totalspent = customer.totalspent
    old_level = customer.levelid.levelid
    
    # 修改订单状态为完成
    print("\n执行操作: 将订单状态改为2（已完成）...")
    order.status = 2
    order.save()
    
    # 刷新客户数据
    customer.refresh_from_db()
    
    print("\n【修改后】")
    show_customer_info(customer.customerid)
    
    # 验证结果
    print("\n【验证结果】")
    expected_totalspent = old_totalspent + order.totalamount
    if customer.totalspent == expected_totalspent:
        print(f"✅ TotalSpent更新正确: {old_totalspent} + {order.totalamount} = {customer.totalspent}")
    else:
        print(f"❌ TotalSpent更新错误: 期望{expected_totalspent}, 实际{customer.totalspent}")
    
    if customer.levelid.levelid != old_level:
        print(f"✅ 信用等级已自动升级: {old_level}级 → {customer.levelid.levelid}级")
    else:
        print(f"ℹ️ 信用等级未变化: {customer.levelid.levelid}级")


def test_order_cancellation():
    """测试订单取消功能"""
    print_separator("测试2: 订单取消后退款")
    
    # 选择一个status=0的订单测试
    order = Orders.objects.filter(status=0).exclude(pk=4).exclude(pk=7).first()
    if not order:
        print("❌ 没有找到合适的订单用于测试")
        return
    
    customer = order.customerid
    print("\n【修改前】")
    print(f"订单ID: {order.orderid}, 金额: ¥{order.totalamount}")
    show_customer_info(customer.customerid)
    
    old_balance = customer.balance
    
    # 修改订单状态为取消
    print("\n执行操作: 将订单状态改为4（已取消）...")
    order.status = 4
    order.save()
    
    # 刷新客户数据
    customer.refresh_from_db()
    
    print("\n【修改后】")
    show_customer_info(customer.customerid)
    
    # 验证结果
    print("\n【验证结果】")
    expected_balance = old_balance + order.totalamount
    if customer.balance == expected_balance:
        print(f"✅ 余额退款正确: {old_balance} + {order.totalamount} = {customer.balance}")
    else:
        print(f"❌ 余额退款错误: 期望{expected_balance}, 实际{customer.balance}")


def show_all_customers():
    """显示所有客户当前状态"""
    print_separator("所有客户当前状态")
    
    customers = Customer.objects.all().order_by('customerid')
    for customer in customers:
        print()
        show_customer_info(customer.customerid)


def show_all_orders():
    """显示所有订单"""
    print_separator("所有订单")
    
    orders = Orders.objects.all().order_by('orderid')
    for order in orders:
        print_separator()
        show_order_info(order.orderid)


def main():
    """主测试流程"""
    print_separator("MyBookwise 客户更新功能测试")
    
    print("\n请选择测试项目:")
    print("1. 查看所有客户状态")
    print("2. 查看所有订单")
    print("3. 测试订单完成（更新TotalSpent）")
    print("4. 测试订单取消（退款）")
    print("5. 查看指定客户信息")
    print("6. 查看指定订单信息")
    print("0. 退出")
    
    try:
        choice = input("\n请输入选项 (0-6): ").strip()
        
        if choice == '1':
            show_all_customers()
        elif choice == '2':
            show_all_orders()
        elif choice == '3':
            test_order_completion()
        elif choice == '4':
            test_order_cancellation()
        elif choice == '5':
            customer_id = int(input("请输入客户ID: "))
            print()
            show_customer_info(customer_id)
        elif choice == '6':
            order_id = int(input("请输入订单ID: "))
            show_order_info(order_id)
        elif choice == '0':
            print("退出测试")
            return
        else:
            print("❌ 无效选项")
            
    except KeyboardInterrupt:
        print("\n\n测试中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

