"""
重置演示数据：恢复 5 个演示顾客的初始余额/信用/等级，
清空订单、缺货记录、采购记录。

图书数据不受影响。

用法（在项目根目录运行）：
  python SetDatabase/reset_demo_data.py
"""

import os
import sys
import django
from decimal import Decimal

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MyBookwise.settings")
django.setup()

from bookstore.models import Customer, Supplier
import django.db as _db

# ─── 初始顾客数据（与 setdatabase.sql 一致）────────────────────────────────
INITIAL_CUSTOMERS = [
    # customerid, balance, levelid_id, creditlimit, usedcredit, totalspent
    (1, Decimal("714.70"),  1, Decimal("0.00"),        Decimal("0.00"),   Decimal("285.30")),
    (2, Decimal("2000.00"), 4, Decimal("1000.00"),      Decimal("209.70"), Decimal("5500.00")),
    (3, Decimal("714.70"),  5, Decimal("99999999.00"),  Decimal("0.00"),   Decimal("12345.30")),
    (4, Decimal("2000.00"), 2, Decimal("0.00"),         Decimal("0.00"),   Decimal("1300.00")),
    (5, Decimal("3000.00"), 3, Decimal("500.00"),       Decimal("0.00"),   Decimal("2022.15")),
]

def reset():
    print("开始重置演示数据...\n")

    conn = _db.connections["default"]
    with conn.cursor() as cur:
        # TRUNCATE 是 DDL，不触发 row-level 触发器（绕过 trg_orderdetail_before_delete）
        # 执行顺序：先子表再父表，避免外键冲突
        cur.execute("SET FOREIGN_KEY_CHECKS=0")
        cur.execute("TRUNCATE TABLE procurementdetail")
        cur.execute("TRUNCATE TABLE procurement")
        cur.execute("TRUNCATE TABLE shortagerecord")
        cur.execute("TRUNCATE TABLE orderdetail")
        cur.execute("TRUNCATE TABLE orders")
        cur.execute("SET FOREIGN_KEY_CHECKS=1")
    conn.commit()
    print("已清空：采购明细 | 采购单 | 缺货记录 | 订单明细 | 订单")

    # 3. 恢复顾客数据
    for cid, balance, levelid, creditlimit, usedcredit, totalspent in INITIAL_CUSTOMERS:
        updated = Customer.objects.filter(customerid=cid).update(
            balance=balance,
            levelid_id=levelid,
            creditlimit=creditlimit,
            usedcredit=usedcredit,
            totalspent=totalspent,
        )
        if updated:
            print(f"已恢复：CustomerID={cid}  余额=¥{balance}  等级={levelid}级")
        else:
            print(f"⚠️  CustomerID={cid} 不存在，跳过")

    # 4. 修复顾客中文姓名和地址（防止 PowerShell 管道恢复后乱码）
    customer_text = [
        (1, '张三', '湖北省武汉市洪山区'),
        (2, '李四', '湖北省武汉市武昌区'),
        (3, '王五', '湖北省武汉市江汉区'),
        (4, '陈六', '湖北省武汉市江夏区'),
        (5, '赵七', '湖北省武汉市东湖区'),
    ]
    for cid, name, addr in customer_text:
        Customer.objects.filter(customerid=cid).update(name=name, address=addr)

    # 5. 修复供应商中文名称和地址
    supplier_text = [
        (1, '北京图书出版社',    '北京市朝阳区',   '010-12345678'),
        (2, '上海文化图书供应商', '上海市浦东新区', '021-87654321'),
        (3, '广州教育图书公司',  '广州市天河区',   '020-11223344'),
    ]
    for sid, name, loc, contact in supplier_text:
        Supplier.objects.filter(supplierid=sid).update(
            suppliername=name, supplylocation=loc, contactinfo=contact
        )

    # 6. 修复图书中文标题和出版社
    from bookstore.models import Book
    book_text = [
        ('978-7-111-54425-7', '深入理解计算机系统', '机械工业出版社',   '计算机,操作系统,底层原理'),
        ('978-7-115-42832-5', 'Python编程：从入门到实践', '人民邮电出版社', 'Python,编程,入门'),
        ('978-7-115-48935-5', '机器学习实战',      '人民邮电出版社',   '机器学习,人工智能,Python'),
        ('978-7-121-35170-9', '算法导论',          '电子工业出版社',   '算法,数据结构,计算机'),
        ('978-7-302-51123-4', '数据库系统概念',    '清华大学出版社',   '数据库,SQL,关系型数据库'),
    ]
    for isbn, title, pub, kw in book_text:
        Book.objects.filter(isbn=isbn).update(title=title, publisher=pub, keywords=kw)

    print("已修复：顾客姓名/地址、供应商名称/地址、原始图书标题/出版社")
    print("\n✅ 演示数据重置完成，图书数据未改动。")

if __name__ == "__main__":
    reset()
