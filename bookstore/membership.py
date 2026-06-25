"""会员等级、积分与畅读卡规则。"""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from .models import Creditlevel, Customer, CustomerProfile

# 会员等级阈值（累计积分）
MEMBER_LEVEL_THRESHOLDS: dict[int, int] = {
    1: 0,
    2: 1000,
    3: 2000,
    4: 5000,
    5: 10000,
}

READING_PASS_DAYS = 30
READING_PASS_DISCOUNT = Decimal("0.72")  # 畅读卡 7.2 折
NON_MEMBER_LEVEL_ID = 0


def get_purchase_discount_rate(customer_id: int) -> Decimal:
    """购书折扣：非会员无折扣，会员按等级（含畅读卡乘算）。"""
    if not is_member(customer_id):
        return Decimal("1")
    return get_effective_discount_rate(customer_id)


def get_display_member_level(customer_id: int) -> int | None:
    """仅已开通会员返回 1–5 级。"""
    if not is_member(customer_id):
        return None
    return calculate_member_level(get_profile(customer_id).points)


def ensure_non_member_level(customer: Customer) -> int:
    """非会员：等级 0，无会员折扣。"""
    if customer.levelid_id == NON_MEMBER_LEVEL_ID:
        return NON_MEMBER_LEVEL_ID
    level = Creditlevel.objects.get(levelid=NON_MEMBER_LEVEL_ID)
    customer.levelid = level
    customer.creditlimit = level.creditlimit
    customer.save(update_fields=["levelid", "creditlimit"])
    return NON_MEMBER_LEVEL_ID


def get_member_level_guide() -> list[dict]:
    """会员等级说明：所需积分与折扣。"""
    rows = []
    for level_id in sorted(MEMBER_LEVEL_THRESHOLDS.keys()):
        cl = Creditlevel.objects.get(levelid=level_id)
        pct = (Decimal("1") - cl.discountrate) * 100
        rows.append(
            {
                "level": level_id,
                "points_required": MEMBER_LEVEL_THRESHOLDS[level_id],
                "discount_rate": str(cl.discountrate),
                "discount_percent": str(pct.quantize(Decimal("0.01"))),
            }
        )
    return rows


def get_profile(customer_id: int) -> CustomerProfile:
    profile, _ = CustomerProfile.objects.get_or_create(
        customer_id=customer_id,
        defaults={"points": 0},
    )
    if profile.member_since is None and profile.points != 0:
        profile.points = 0
        profile.save(update_fields=["points", "updated_at"])
    if profile.member_since is None:
        ensure_non_member_level(Customer.objects.get(pk=customer_id))
    return profile


def is_member(customer_id: int) -> bool:
    profile = get_profile(customer_id)
    return profile.member_since is not None


def has_reading_pass(customer_id: int) -> bool:
    profile = get_profile(customer_id)
    exp = profile.reading_pass_expires_at
    return bool(exp and exp > timezone.now())


def calculate_member_level(points: int) -> int:
    level = 1
    for lvl, threshold in sorted(MEMBER_LEVEL_THRESHOLDS.items()):
        if points >= threshold:
            level = lvl
    return level


def next_level_points(points: int) -> int | str | None:
    current = calculate_member_level(points)
    if current >= 5:
        return "max"
    nxt = current + 1
    need = MEMBER_LEVEL_THRESHOLDS.get(nxt)
    if need is None:
        return "max"
    remaining = need - points
    return max(0, remaining)


def sync_member_level(customer: Customer, points: int | None = None) -> int:
    if not is_member(customer.customerid):
        return ensure_non_member_level(customer)
    if points is None:
        points = get_profile(customer.customerid).points
    level_id = calculate_member_level(points)
    level = Creditlevel.objects.get(levelid=level_id)
    customer.levelid = level
    customer.creditlimit = level.creditlimit
    customer.save(update_fields=["levelid", "creditlimit"])
    return level_id


def get_effective_discount_rate(customer_id: int) -> Decimal:
    """会员等级折扣 × 畅读卡折扣（须已开通会员）。"""
    if not is_member(customer_id):
        return Decimal("1")
    customer = Customer.objects.select_related("levelid").get(pk=customer_id)
    base = customer.levelid.discountrate
    if has_reading_pass(customer_id):
        return (base * READING_PASS_DISCOUNT).quantize(Decimal("0.0001"))
    return base


def reading_pass_multiplier(customer_id: int) -> Decimal:
    """订单触发器已按等级折扣算价后，畅读卡再乘的系数。"""
    return READING_PASS_DISCOUNT if has_reading_pass(customer_id) else Decimal("1")


def activate_free_membership(customer_id: int) -> CustomerProfile:
    profile = get_profile(customer_id)
    if profile.member_since is None:
        profile.member_since = timezone.now()
        profile.save(update_fields=["member_since", "updated_at"])
    sync_member_level(Customer.objects.get(pk=customer_id))
    return profile


def activate_reading_pass(customer_id: int, days: int = READING_PASS_DAYS) -> CustomerProfile:
    profile = get_profile(customer_id)
    if not is_member(customer_id):
        activate_free_membership(customer_id)
    now = timezone.now()
    base = (
        profile.reading_pass_expires_at
        if profile.reading_pass_expires_at and profile.reading_pass_expires_at > now
        else now
    )
    profile.reading_pass_expires_at = base + timedelta(days=days)
    profile.save(update_fields=["reading_pass_expires_at", "updated_at"])
    return profile


def add_points(customer_id: int, points: int) -> int:
    if points <= 0:
        return get_profile(customer_id).points
    profile = get_profile(customer_id)
    profile.points += points
    profile.save(update_fields=["points", "updated_at"])
    sync_member_level(Customer.objects.get(pk=customer_id), profile.points)
    return profile.points


def award_order_points(customer_id: int, amount: Decimal) -> int:
    """仅会员可获得积分，与人民币 1:1。"""
    if not is_member(customer_id):
        return get_profile(customer_id).points
    earned = int(amount)
    if earned <= 0:
        return get_profile(customer_id).points
    return add_points(customer_id, earned)


def apply_reading_pass_to_order_total(customer_id: int, order_total: Decimal) -> Decimal:
    """触发器按等级折扣算价后，畅读卡折扣乘算。"""
    mult = reading_pass_multiplier(customer_id)
    if mult == Decimal("1"):
        return order_total
    return (order_total * mult).quantize(Decimal("0.01"))


def serialize_membership(customer_id: int) -> dict:
    profile = get_profile(customer_id)
    member = is_member(customer_id)
    reading = has_reading_pass(customer_id)
    nxt = next_level_points(profile.points) if member else None
    effective = get_effective_discount_rate(customer_id) if member else None
    display_level = get_display_member_level(customer_id)
    return {
        "points": profile.points,
        "is_member": member,
        "member_level": display_level,
        "member_since": profile.member_since.isoformat() if profile.member_since else None,
        "has_reading_pass": reading,
        "reading_pass_expires_at": (
            profile.reading_pass_expires_at.isoformat()
            if profile.reading_pass_expires_at
            else None
        ),
        "next_level_points": str(nxt) if nxt is not None else None,
        "effective_discount_rate": str(effective) if effective is not None else None,
        "effective_discount_percent": str(
            ((Decimal("1") - effective) * 100).quantize(Decimal("0.01"))
        )
        if effective is not None
        else None,
    }
