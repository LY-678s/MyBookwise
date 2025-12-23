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
    # Use atomic transaction and select_for_update on customer to ensure consistency
    with transaction.atomic():
        customer = Customer.objects.select_for_update().select_related('levelid').get(pk=instance.customerid_id)
        creditlevel = customer.levelid

        # 1) Deduct difference when TotalAmount changes and status=0
        if instance.totalamount is not None and (old_totalamount != instance.totalamount) and instance.status == 0:
            amount_diff = instance.totalamount - (old_totalamount or 0)
            if amount_diff != 0:
                # Determine overdraft policy: prefer customer's overdraftlimit if present
                overdraft_limit = customer.overdraftlimit or creditlevel.overdraftlimit
                can_overdraft = creditlevel.candoverdraft
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

        # 2) Refund when order cancelled (status becomes 4)
        if instance.status == 4 and old_status != 4 and instance.totalamount is not None:
            customer.balance = customer.balance + instance.totalamount
            # If order was previously completed, reduce TotalSpent
            if old_status == 2:
                customer.totalspent = max(customer.totalspent - (instance.totalamount or 0), 0)
            customer.save(update_fields=['balance', 'totalspent'])

        # 3) When order becomes completed, add to TotalSpent
        if instance.status == 2 and old_status != 2 and instance.totalamount is not None:
            customer.totalspent = (customer.totalspent or 0) + instance.totalamount
            customer.save(update_fields=['totalspent'])


@receiver(pre_save, sender=Orders)
def orders_capture_old(sender, instance, **kwargs):
    # attach old values to instance for use in post_save
    old_status, old_total = _get_old_order_values(instance)
    instance._old_status = old_status
    instance._old_totalamount = old_total


@receiver(post_save, sender=Orders)
def orders_post_save(sender, instance, created, **kwargs):
    old_status = getattr(instance, '_old_status', None)
    old_totalamount = getattr(instance, '_old_totalamount', None)
    try:
        _handle_deduct_or_refund(instance, old_status, old_totalamount)
    except ValidationError as e:
        # Re-raise so admin/view layer can catch and display friendly message
        raise
    except Exception:
        logging.exception("Error processing Orders post_save")



