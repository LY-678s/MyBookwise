from decimal import Decimal
import logging

from django.db import transaction, models
from django.db.models.signals import post_save
from django.db.models import F, Sum
from django.dispatch import receiver
from django.utils import timezone

from .models import (
    Shortagerecord,
    Supplierbook,
    Procurement,
    Procurementdetail,
)

# 启动时打印，确认signals.py被加载
print("="*60)
print("🚀 bookstore/signals.py loaded successfully!")
print("="*60)


@receiver(post_save, sender=Shortagerecord)
def handle_shortagerecord_post_save(sender, instance, created, **kwargs):
    """
    When a Shortagerecord is created or updated to Status=0 (unprocessed),
    generate procurement and procurement detail in application layer,
    then mark Shortagerecord.status = 2 (generated) using queryset.update()
    to avoid retriggering signals.
    """
    # Only handle unprocessed shortage records
    try:
        if instance.status != 0:
            return

        with transaction.atomic():
            # Find preferred supplier for this ISBN
            sb = Supplierbook.objects.filter(
                isbn=instance.isbn,
                supplierid__isactive=1
            ).order_by('supplyprice', '-lastsupplydate').first()

            if not sb:
                # No active supplier available; nothing to do
                return

            supplier = sb.supplierid
            supply_price = sb.supplyprice or Decimal('0.00')

            # Reuse existing open procurement for supplier if exists
            proc = Procurement.objects.filter(supplierid=supplier, status=0).first()

            if proc is None:
                # Generate ProcNo of form PC-000001
                max_num = 0
                for procno in Procurement.objects.filter(procno__startswith='PC-').values_list('procno', flat=True):
                    try:
                        num = int(procno[3:])
                        if num > max_num:
                            max_num = num
                    except Exception:
                        continue
                new_num = max_num + 1
                procno = f"PC-{new_num:06d}"

                proc = Procurement.objects.create(
                    procno=procno,
                    supplierid=supplier,
                    recordid=instance,
                    createdate=timezone.now(),
                    status=0,
                )

            # Insert or update procurement detail
            pd_qs = Procurementdetail.objects.filter(procid=proc, isbn=instance.isbn)
            if not pd_qs.exists():
                Procurementdetail.objects.create(
                    procid=proc,
                    isbn=instance.isbn,
                    quantity=instance.quantity,
                    supplyprice=supply_price,
                    receivedqty=0,
                )
            else:
                pd_qs.update(quantity=F('quantity') + instance.quantity)

            # Update shortage record status to 'generated' (2) without calling save()
            Shortagerecord.objects.filter(pk=instance.pk).update(status=2)

    except Exception:
        logging.exception("Error processing Shortagerecord post_save")


from django.db.models.signals import pre_save
from django.core.exceptions import ValidationError

# Use explicit import to avoid circular import issues in signal registration
from .models import Orders, Customer, Creditlevel


def process_payment(order, customer):
    """
    处理订单付款逻辑
    - 扣除余额（可能透支）
    - 更新ActualPaid, PaymentStatus
    - 增加TotalSpent
    - 可能升级信用等级
    - 更新CurrentOverdraft
    
    Args:
        order: Orders对象
        customer: Customer对象（需要已select_for_update锁定）
    
    Returns:
        (success, message): (True, "成功消息") 或 (False, "错误消息")
    """
    from decimal import Decimal
    from .models import Creditlevel
    
    creditlevel = customer.levelid
    amount = order.totalamount or Decimal('0')
    
    # 检查透支额度
    new_balance = customer.balance - amount
    overdraft_needed = max(-new_balance, Decimal('0'))  # 需要的透支金额
    
    # 1-2级不能透支
    if creditlevel.canoverdraft == 0 and new_balance < 0:
        return False, f"余额不足（{customer.balance}元），该信用等级不允许透支，请充值"
    
    # 3-5级检查透支限额
    if creditlevel.canoverdraft == 1:
        if overdraft_needed > customer.overdraftlimit:
            return False, f"余额不足，需要透支{overdraft_needed}元，超出透支额度{customer.overdraftlimit}元，请充值"
    
    # 扣款
    old_balance = customer.balance
    old_totalspent = customer.totalspent
    old_level = customer.levelid.levelid
    
    customer.balance = new_balance
    customer.totalspent = (customer.totalspent or Decimal('0')) + amount
    
    # 重新计算透支金额（考虑其他未付款订单）
    customer.currentoverdraft = calculate_current_overdraft(customer)
    
    # 检查信用等级升级
    new_level_id = _calculate_credit_level(customer.totalspent)
    if new_level_id != old_level:
        customer.levelid = Creditlevel.objects.get(levelid=new_level_id)
    
    customer.save(update_fields=['balance', 'currentoverdraft', 'totalspent', 'levelid'])
    
    print(f"   💰 [PAYMENT] Paid {amount}")
    print(f"   Balance: {old_balance} → {customer.balance}")
    print(f"   CurrentOverdraft: 0 → {customer.currentoverdraft}")
    print(f"   TotalSpent: {old_totalspent} → {customer.totalspent}")
    if new_level_id != old_level:
        print(f"   🎖️ Level upgraded: {old_level} → {new_level_id}")
    
    return True, f"付款成功！余额：{customer.balance}元"


def calculate_current_overdraft(customer):
    """
    计算客户的当前透支金额
    = 负余额的绝对值 + 未付款订单总额
    """
    from decimal import Decimal
    from .models import Orders
    
    # 1. 负余额部分
    negative_balance = abs(min(customer.balance, Decimal('0')))
    
    # 2. 未付款订单总额
    unpaid_orders_total = Orders.objects.filter(
        customerid=customer,
        paymentstatus=0,  # 未付款
        status__in=[0, 1]  # 排除已取消的订单
    ).aggregate(
        total=models.Sum('totalamount')
    )['total'] or Decimal('0')
    
    return negative_balance + unpaid_orders_total


def _calculate_credit_level(totalspent):
    """
    根据累计消费金额计算信用等级
    规则：
    - TotalSpent >= 10000 → 5级
    - TotalSpent >= 5000  → 4级
    - TotalSpent >= 2000  → 3级
    - TotalSpent >= 1000  → 2级
    - 否则               → 1级
    """
    from decimal import Decimal
    totalspent = Decimal(str(totalspent)) if totalspent else Decimal('0')
    
    if totalspent >= Decimal('10000'):
        return 5
    elif totalspent >= Decimal('5000'):
        return 4
    elif totalspent >= Decimal('2000'):
        return 3
    elif totalspent >= Decimal('1000'):
        return 2
    else:
        return 1


def _get_old_order_values(instance):
    """Return (old_status, old_totalamount) for existing order, or (None, None) for new."""
    if not instance.pk:
        return None, None
    try:
        old = Orders.objects.get(pk=instance.pk)
        return old.status, old.totalamount
    except Orders.DoesNotExist:
        return None, None


def _handle_deduct_or_refund(instance, old_status, old_totalamount):
    """
    新的付款和退款逻辑：
    - 只有实付金额（ActualPaid）才增加TotalSpent
    - 订单取消时退款并设置PaymentStatus=2
    """
    print(f"🟢 [HANDLE] Starting _handle_deduct_or_refund")
    print(f"   Order: {instance.orderid}, Status: {old_status}→{instance.status}")
    print(f"   Amount: {instance.totalamount}, ActualPaid: {instance.actualpaid}, PaymentStatus: {instance.paymentstatus}")
    
    # Use atomic transaction and select_for_update on customer to ensure consistency
    with transaction.atomic():
        customer = Customer.objects.select_for_update().select_related('levelid').get(pk=instance.customerid_id)
        creditlevel = customer.levelid
        
        print(f"   Customer: {customer.name} (ID={customer.customerid})")
        print(f"   Before: Balance={customer.balance}, CurrentOverdraft={customer.currentoverdraft}, TotalSpent={customer.totalspent}, Level={customer.levelid.levelid}")

        # 暂时保留原有扣款逻辑（用于订单金额变化时的差额调整）
        # 实际付款逻辑将在前台视图中处理
        pass  # 这部分逻辑将由新的payment函数处理

        # 2) Refund when order cancelled (status becomes 4)
        if instance.status == 4 and old_status != 4:
            print(f"   💸 [REFUND] Processing refund...")
            old_level = customer.levelid.levelid
            
            # 只退还实际已付的金额
            if instance.actualpaid > 0:
                customer.balance = customer.balance + instance.actualpaid
                # 减少TotalSpent（因为付款时已增加，现在退款要减回去）
                customer.totalspent = max(customer.totalspent - instance.actualpaid, 0)
                
                # 更新CurrentOverdraft（退款后可能减少透支）
                if customer.balance < 0:
                    customer.currentoverdraft = abs(customer.balance)
                else:
                    customer.currentoverdraft = 0
                
                # 检查是否需要降级
                new_level_id = _calculate_credit_level(customer.totalspent)
                if new_level_id != old_level:
                    from .models import Creditlevel
                    customer.levelid = Creditlevel.objects.get(levelid=new_level_id)
                    customer.save(update_fields=['balance', 'currentoverdraft', 'totalspent', 'levelid'])
                    print(f"   ✅ Refund: Balance={customer.balance}, TotalSpent={customer.totalspent}")
                    print(f"   ⬇️ Level downgraded: {old_level} → {new_level_id}")
                else:
                    customer.save(update_fields=['balance', 'currentoverdraft', 'totalspent'])
                    print(f"   ✅ Refund: Balance={customer.balance}, TotalSpent={customer.totalspent}")
            else:
                print(f"   ℹ️ No refund needed (ActualPaid=0)")

        # 3) When order becomes completed - 不再更新TotalSpent（在付款时已更新）
        if instance.status == 2 and old_status != 2:
            print(f"   ✅ [COMPLETE] Order completed (TotalSpent already updated at payment time)")


@receiver(pre_save, sender=Orders)
def orders_capture_old(sender, instance, **kwargs):
    # attach old values to instance for use in post_save
    old_status, old_total = _get_old_order_values(instance)
    instance._old_status = old_status
    instance._old_totalamount = old_total
    
    # 调试信息
    print(f"\n{'='*60}")
    print(f"🔵 [PRE_SAVE] Order {instance.orderid}")
    print(f"   Old Status: {old_status} → New Status: {instance.status}")
    print(f"   Old Amount: {old_total} → New Amount: {instance.totalamount}")
    print(f"   Customer ID: {instance.customerid_id}")
    print(f"{'='*60}\n")


@receiver(post_save, sender=Orders)
def orders_post_save(sender, instance, created, **kwargs):
    old_status = getattr(instance, '_old_status', None)
    old_totalamount = getattr(instance, '_old_totalamount', None)
    
    # 调试日志
    print(f"🔔 [Signal] Order {instance.orderid} saved: old_status={old_status}, new_status={instance.status}, amount={instance.totalamount}")
    
    try:
        _handle_deduct_or_refund(instance, old_status, old_totalamount)
        print(f"✅ [Signal] Order {instance.orderid} processed successfully")
    except ValidationError as e:
        print(f"❌ [Signal] ValidationError for Order {instance.orderid}: {e}")
        # Re-raise so admin/view layer can catch and display friendly message
        raise
    except Exception as e:
        print(f"❌ [Signal] Exception for Order {instance.orderid}: {e}")
        logging.exception("Error processing Orders post_save")



