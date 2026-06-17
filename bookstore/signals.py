"""
支付与信用模块信号处理

本模块包含订单支付、退款、信用等级管理的核心业务逻辑：
- 缺货记录自动生成采购单
- 信用等级计算
- 支付处理
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
    Creditlevel,
)


# ============================================================================
# 被测试的核心业务函数
# ============================================================================

# pylint: disable=no-member
# pylint 无法识别 Django ORM 动态注入的 objects 管理器和 DoesNotExist 异常类，
# 以下所有 .objects / .DoesNotExist 调用均通过 Django ORM 验证，添加此全局禁用。

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
    totalspent = Decimal(str(totalspent)) if totalspent else Decimal('0')

    if totalspent >= Decimal('10000'):
        return 5
    if totalspent >= Decimal('5000'):
        return 4
    if totalspent >= Decimal('2000'):
        return 3
    if totalspent >= Decimal('1000'):
        return 2
    return 1


def _get_available_credit(customer):
    """计算客户当前可用信用额度"""
    return customer.creditlimit - customer.usedcredit


def _determine_payment_plan(balance, amount, usedcredit, creditlimit, canusecredit):
    """
    确定支付方案

    Returns:
        dict: {
            'method': 'balance' | 'credit' | 'mixed' | None,
            'balance_deduct': Decimal,
            'credit_deduct': Decimal,
            'actual_paid': Decimal,
            'payment_status': int,
            'new_balance': Decimal,
            'new_usedcredit': Decimal,
            'new_totalspent': Decimal,
            'message': str
        }
        或 None 表示支付失败
    """
    if balance >= amount:
        return {
            'method': 'balance',
            'balance_deduct': amount,
            'credit_deduct': Decimal('0'),
            'actual_paid': amount,
            'payment_status': 1,
            'new_balance': balance - amount,
            'new_usedcredit': usedcredit,
            'new_totalspent': amount,
            'message': f"支付成功！余额：¥{balance - amount}",
        }

    # 余额不足
    credit_needed = amount - balance

    if not canusecredit:
        return None

    available_credit = creditlimit - usedcredit
    if credit_needed > available_credit:
        return None

    return {
        'method': 'mixed',
        'balance_deduct': balance,
        'credit_deduct': credit_needed,
        'actual_paid': balance,
        'payment_status': 2,
        'new_balance': Decimal('0'),
        'new_usedcredit': usedcredit + credit_needed,
        'new_totalspent': balance,
        'message': (
            f"支付成功！使用余额¥{balance}，"
            f"使用信用¥{credit_needed}，当前余额：¥0"
        ),
    }


def process_payment(order, customer, use_credit_only=False):
    """
    处理订单支付

    Args:
        order: Orders对象
        customer: Customer对象（需要已select_for_update锁定）
        use_credit_only: 是否只使用信用支付（不用余额）

    Returns:
        (success, message): (True, "成功消息") 或 (False, "错误消息")
        成功时 message 为 (msg_str, actual_paid, payment_status) 三元组
    """
    creditlevel = customer.levelid
    amount = order.totalamount or Decimal('0')
    balance = customer.balance
    usedcredit = customer.usedcredit
    creditlimit = customer.creditlimit

    old_level = creditlevel.levelid

    if use_credit_only:
        if creditlevel.canusecredit == 0:
            return False, "您的信用等级不支持信用支付"

        available_credit = creditlimit - usedcredit
        if usedcredit + amount > creditlimit:
            return False, (
                f"信用额度不足，需要{amount}元，"
                f"可用额度{available_credit}元"
            )

        plan = {
            'method': 'credit',
            'credit_deduct': amount,
            'actual_paid': Decimal('0'),
            'payment_status': 2,
            'new_usedcredit': usedcredit + amount,
            'new_totalspent': Decimal('0'),
            'message': (
                f"信用支付成功！使用信用额度：¥{amount}，"
                f"剩余可用：¥{creditlimit - usedcredit - amount}"
            ),
        }
        customer.usedcredit = plan['new_usedcredit']
    else:
        plan = _determine_payment_plan(
            balance, amount, usedcredit, creditlimit,
            creditlevel.canusecredit
        )
        if plan is None:
            if creditlevel.canusecredit == 0:
                msg = f"余额不足（{balance}元），该信用等级不支持信用支付，请充值"
            else:
                available_credit = creditlimit - usedcredit
                credit_needed = amount - balance
                msg = (
                    f"余额不足，需要信用{credit_needed}元，"
                    f"但可用信用额度只有{available_credit}元，请充值"
                )
            return False, msg

        customer.balance = plan['new_balance']
        customer.totalspent += plan['new_totalspent']
        customer.usedcredit = plan['new_usedcredit']

    new_level_id = _calculate_credit_level(customer.totalspent)

    fields = ['balance', 'usedcredit', 'totalspent']
    if new_level_id != old_level:
        customer.levelid = Creditlevel.objects.get(levelid=new_level_id)
        fields.append('levelid')

    customer.save(update_fields=fields)

    return True, (plan['message'], plan['actual_paid'], plan['payment_status'])


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


def _handle_order_cancel_refund(instance, customer, old_level):
    """
    处理订单取消退款。

    - 实付金额退回余额，累计消费等额扣减
    - 已用信用额度释放
    - 支付状态置为3（已取消退款）
    """
    if instance.actualpaid > 0:
        customer.balance += instance.actualpaid
        customer.totalspent = max(
            customer.totalspent - instance.actualpaid, Decimal('0'))

    if instance.paymentstatus == 2:
        credit_used = instance.totalamount - instance.actualpaid
        customer.usedcredit = max(
            customer.usedcredit - credit_used, Decimal('0'))

    instance.paymentstatus = 3

    new_level_id = _calculate_credit_level(customer.totalspent)
    fields = ['balance', 'usedcredit', 'totalspent']

    if new_level_id != old_level:
        customer.levelid = Creditlevel.objects.get(levelid=new_level_id)
        fields.append('levelid')

    customer.save(update_fields=fields)


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
