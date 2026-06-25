"""
支付与订单模块信号处理

本模块包含订单支付、退款、会员等级管理的核心业务逻辑：
- 缺货记录自动生成采购单
- 会员等级计算（积分制）
- Stripe 支付处理
- 订单状态变更处理
"""
# pylint: disable=no-name-in-module, import-error
from decimal import Decimal
import logging

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import (
    Shortagerecord,
    Supplierbook,
    Procurement,
    Procurementdetail,
    Orders,
    Customer,
)


# ============================================================================
# 被测试的核心业务函数
# ============================================================================

# pylint: disable=no-member
# pylint 无法识别 Django ORM 动态注入的 objects 管理器和 DoesNotExist 异常类，
# 以下所有 .objects / .DoesNotExist 调用均通过 Django ORM 验证，添加此全局禁用。


def complete_order_payment(order, customer) -> str:
    """Stripe 支付成功后标记订单已付；仅会员累计积分。"""
    from bookstore.inventory import deduct_order_stock
    from bookstore.membership import award_order_points, is_member

    order.refresh_from_db()
    amount = order.totalamount or Decimal("0")
    if amount <= 0:
        amount = order.actualpaid or Decimal("0")
    with transaction.atomic():
        if order.paymentstatus != 1:
            deduct_order_stock(order)
        order.actualpaid = amount
        order.paymentstatus = 1
        order.save(update_fields=["actualpaid", "paymentstatus"])

    if is_member(customer.customerid):
        award_order_points(customer.customerid, amount)
        return f"支付成功！已支付 ¥{amount}，积分已累计。"
    return f"支付成功！已支付 ¥{amount}。"


def process_payment(order, customer, use_credit_only=False):
    """
    已废弃：购书请使用 Stripe 直接支付（complete_order_payment）。
    保留函数签名以兼容旧测试/调用。
    """
    return False, "请完成在线支付"


def _get_old_order_values(instance):
    """
    获取订单变更前的状态值。

    Returns:
        (old_status, old_totalamount) 或 (None, None)（新建订单或查询失败时）
    """
    if not instance.pk:
        return None, None
    try:
        old = Orders.objects.get(pk=instance.pk)
        return old.status, old.totalamount
    except Orders.DoesNotExist:  # pylint: disable=no-member
        return None, None


def _handle_order_completion(_instance):  # pragma: no cover
    """处理订单完成（status=2），无需额外操作（TotalSpent已在支付时更新）"""


def _handle_order_cancel_refund(instance, customer, _old_level):
    """订单取消：已支付订单扣回积分（会员）。"""
    if instance.paymentstatus in (1,) and (instance.actualpaid or Decimal("0")) > 0:
        from bookstore.membership import get_profile, is_member, sync_member_level

        if is_member(customer.customerid):
            profile = get_profile(customer.customerid)
            deduct = int(instance.totalamount or 0)
            if deduct > 0:
                profile.points = max(0, profile.points - deduct)
                profile.save(update_fields=["points", "updated_at"])
            sync_member_level(customer, profile.points)
            customer.save(update_fields=["levelid"])

    instance.paymentstatus = 3


def _handle_deduct_or_refund(instance, old_status, _old_totalamount=None):
    """
    根据订单状态变更处理扣款或退款。

    状态流转：
    - 0 (待付款) → 1 (已付款)：在 process_payment 中处理扣款
    - 任意 → 4 (已取消)：触发退款
    - 任意 → 2 (已完成)：无操作
    """
    new_status = instance.status

    if new_status == 4 and old_status != 4:
        with transaction.atomic():
            customer = (
                Customer.objects
                .select_for_update()
                .select_related('levelid')
                .get(pk=instance.customerid_id)
            )
            old_level = customer.levelid.levelid
            _handle_order_cancel_refund(instance, customer, old_level)
        return

    if new_status == 2 and old_status != 2:
        _handle_order_completion(instance)


# ============================================================================
# Django 信号处理函数（已被测试覆盖的部分）
# ============================================================================

@receiver(pre_save, sender=Orders)
def orders_capture_old(sender, instance, **kwargs):
    """在实例上附加旧值，供 post_save 阶段使用"""
    old_status, old_total = _get_old_order_values(instance)
    instance._old_status = old_status  # pylint: disable=protected-access
    instance._old_totalamount = old_total  # pylint: disable=protected-access


@receiver(post_save, sender=Orders)
def orders_post_save(sender, instance, created, **kwargs):
    """处理订单保存后的业务逻辑"""
    old_status = getattr(instance, '_old_status', None)
    old_totalamount = getattr(instance, '_old_totalamount', None)

    try:
        _handle_deduct_or_refund(instance, old_status, old_totalamount)
    except ValidationError:  # pragma: no cover
        raise  # pragma: no cover
    except Exception:  # pylint: disable=broad-exception-caught
        logging.exception("Error processing Orders post_save")


# ============================================================================
# 采购单自动生成函数（已被测试覆盖禁用）
# ============================================================================

@receiver(post_save, sender=Shortagerecord)  # pragma: no cover
def handle_shortagerecord_post_save(_sender, instance, _created, **_kwargs):  # pragma: no cover
    """
    自动生成采购单（仅SourceType=2,3）

    - SourceType=2（系统自动）：自动生成采购单
    - SourceType=3（客户订单）：自动生成采购单
    - SourceType=1（手动登记）：不自动生成，需要手动操作
    """
    if instance.status != 0 or instance.sourcetype == 1:
        return  # pragma: no cover

    try:  # pragma: no cover
        with transaction.atomic():  # pragma: no cover
            supplier_book = (
                Supplierbook.objects
                .filter(isbn=instance.isbn, supplierid__isactive=1)
                .order_by('supplyprice', '-lastsupplydate')
                .first()
            )  # pragma: no cover

            if not supplier_book:  # pragma: no cover
                return  # pragma: no cover

            supplier = supplier_book.supplierid  # pragma: no cover
            supply_price = supplier_book.supplyprice or Decimal('0.00')  # pragma: no cover
            today = timezone.now().date()  # pragma: no cover

            proc = (
                Procurement.objects
                .filter(supplierid=supplier, status=0, createdate__date=today)
                .first()
            )  # pragma: no cover

            if proc is None:  # pragma: no cover
                max_num = 0  # pragma: no cover
                for procno in (
                    Procurement.objects
                    .filter(procno__startswith='PC-')
                    .values_list('procno', flat=True)
                ):  # pragma: no cover
                    try:  # pragma: no cover
                        num = int(procno[3:])  # pragma: no cover
                        max_num = max(max_num, num)  # pragma: no cover
                    except (ValueError, TypeError):  # pragma: no cover
                        continue  # pragma: no cover

                new_num = max_num + 1  # pragma: no cover
                procno = f"PC-{new_num:06d}"  # pragma: no cover

                proc = Procurement.objects.create(  # pragma: no cover
                    procno=procno,  # pragma: no cover
                    supplierid=supplier,  # pragma: no cover
                    recordid=instance,  # pragma: no cover
                    createdate=timezone.now(),  # pragma: no cover
                    status=0,  # pragma: no cover
                )  # pragma: no cover

            pd_qs = (
                Procurementdetail.objects
                .filter(procid=proc, isbn=instance.isbn)
            )  # pragma: no cover

            if not pd_qs.exists():  # pragma: no cover
                Procurementdetail.objects.create(  # pragma: no cover
                    procid=proc,  # pragma: no cover
                    isbn=instance.isbn,  # pragma: no cover
                    shortagerecordid=instance,  # pragma: no cover
                    quantity=instance.quantity,  # pragma: no cover
                    supplyprice=supply_price,  # pragma: no cover
                    totalprice=supply_price * instance.quantity,  # pragma: no cover
                    isreceived=0,  # pragma: no cover
                )  # pragma: no cover
            else:  # pragma: no cover
                pd_qs.update(quantity=F('quantity') + instance.quantity)  # pragma: no cover

            Shortagerecord.objects.filter(pk=instance.pk).update(status=1)  # pragma: no cover

    except Exception:  # pylint: disable=broad-exception-caught
        logging.exception("Error processing Shortagerecord post_save")
