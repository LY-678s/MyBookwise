from decimal import Decimal
import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.db.models import F
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
    Perform customer balance deduction/refund and TotalSpent updates in application layer.
    This mirrors previous trigger logic but runs in Django for correctness and to avoid MySQL 1442.
    """
    print(f"🟢 [HANDLE] Starting _handle_deduct_or_refund")
    print(f"   Order: {instance.orderid}, Status: {old_status}→{instance.status}, Amount: {instance.totalamount}")
    
    # Use atomic transaction and select_for_update on customer to ensure consistency
    with transaction.atomic():
        customer = Customer.objects.select_for_update().select_related('levelid').get(pk=instance.customerid_id)
        creditlevel = customer.levelid
        
        print(f"   Customer: {customer.name} (ID={customer.customerid})")
        print(f"   Before: Balance={customer.balance}, TotalSpent={customer.totalspent}, Level={customer.levelid.levelid}")

        # 1) Deduct difference when TotalAmount changes and status=0
        if instance.totalamount is not None and (old_totalamount != instance.totalamount) and instance.status == 0:
            print(f"   💰 [DEDUCT] Deducting balance...")
            amount_diff = instance.totalamount - (old_totalamount or 0)
            if amount_diff != 0:
                # Determine overdraft policy: prefer customer's overdraftlimit if present
                overdraft_limit = customer.overdraftlimit or creditlevel.overdraftlimit
                can_overdraft = creditlevel.canoverdraft
                new_balance = customer.balance - amount_diff
                if can_overdraft == 0:
                    if new_balance < 0:
                        raise ValidationError("余额不足，该信用等级不允许透支")
                else:
                    if overdraft_limit < 999999:
                        if new_balance < -overdraft_limit:
                            raise ValidationError("余额不足，超出透支额度")
                # All checks passed; update balance
                customer.balance = new_balance
                customer.save(update_fields=['balance'])
                print(f"   ✅ Balance updated: {customer.balance}")

        # 2) Refund when order cancelled (status becomes 4)
        if instance.status == 4 and old_status != 4 and instance.totalamount is not None:
            print(f"   💸 [REFUND] Processing refund...")
            old_level = customer.levelid.levelid
            customer.balance = customer.balance + instance.totalamount
            # If order was previously completed, reduce TotalSpent
            if old_status == 2:
                customer.totalspent = max(customer.totalspent - (instance.totalamount or 0), 0)
                
                # 检查是否需要降级
                new_level_id = _calculate_credit_level(customer.totalspent)
                if new_level_id != old_level:
                    from .models import Creditlevel
                    customer.levelid = Creditlevel.objects.get(levelid=new_level_id)
                    customer.save(update_fields=['balance', 'totalspent', 'levelid'])
                    print(f"   ✅ Refund completed: Balance={customer.balance}, TotalSpent={customer.totalspent}")
                    print(f"   ⬇️ Level downgraded: {old_level} → {new_level_id}")
                else:
                    customer.save(update_fields=['balance', 'totalspent'])
                    print(f"   ✅ Refund completed: Balance={customer.balance}, TotalSpent={customer.totalspent}")
            else:
                customer.save(update_fields=['balance'])
                print(f"   ✅ Refund completed: Balance={customer.balance}")

        # 3) When order becomes completed, add to TotalSpent
        if instance.status == 2 and old_status != 2 and instance.totalamount is not None:
            print(f"   📈 [COMPLETE] Adding to TotalSpent...")
            print(f"      Condition check: status={instance.status}, old_status={old_status}, amount={instance.totalamount}")
            old_totalspent = customer.totalspent
            old_level = customer.levelid.levelid
            customer.totalspent = (customer.totalspent or 0) + instance.totalamount
            
            # 根据新的TotalSpent计算应该的信用等级
            new_level_id = _calculate_credit_level(customer.totalspent)
            
            # 如果等级需要变化，同时更新
            if new_level_id != old_level:
                from .models import Creditlevel
                customer.levelid = Creditlevel.objects.get(levelid=new_level_id)
                customer.save(update_fields=['totalspent', 'levelid'])
                print(f"   ✅ TotalSpent updated: {old_totalspent} + {instance.totalamount} = {customer.totalspent}")
                print(f"   🎖️ Level upgraded: {old_level} → {new_level_id} ⭐")
            else:
                customer.save(update_fields=['totalspent'])
                print(f"   ✅ TotalSpent updated: {old_totalspent} + {instance.totalamount} = {customer.totalspent}")
                print(f"   ℹ️ Level unchanged: {customer.levelid.levelid}")


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



