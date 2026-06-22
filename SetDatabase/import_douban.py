"""
将 book_douban.csv 直接插入 MySQL（用 Django settings 的数据库配置）。
不经过 PowerShell 管道，彻底避免 UTF-8 乱码。

用法（在项目根目录运行）：
  python SetDatabase/import_douban.py
"""

import csv
import os
import random
import re
import sys
import django

# ── Django 环境初始化 ───────────────────────────────────────────────────────
# 脚本可在项目根目录运行，也支持从 SetDatabase/ 内运行
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MyBookwise.settings")
django.setup()

import django.db as _db

INPUT_CSV       = os.path.join(os.path.dirname(__file__), "book_douban.csv")
MAX_BOOKS       = 1000
MIN_STOCK_LIMIT = 10       # 固定最低库存，不随机（内部用于触发缺货/采购逻辑）

LOCATIONS = [
    "A-01", "A-02", "A-03", "A-04", "A-05",
    "B-01", "B-02", "B-03", "B-04", "B-05",
    "C-01", "C-02", "C-03",
]


# ─── 工具 ─────────────────────────────────────────────────────────────────────

def clean(s):
    if s is None:
        return None
    s = str(s).strip()
    return None if s.lower() in ("none", "", "nan", "null") else s

def is_valid_isbn13(s):
    return len(re.sub(r"\D", "", s or "")) == 13

def is_chinese(title):
    return sum(1 for c in (title or "") if "\u4e00" <= c <= "\u9fff") >= 2

def cover_url(isbn):
    return (
        f"https://books.google.com/books/content?"
        f"vid=ISBN:{isbn}&printsec=frontcover&img=1&zoom=1&source=gbs_api"
    )

def random_price():
    return f"{random.choice(range(19, 200, 10))}.90"

def random_stock():
    return max(5, min(200, int(random.gauss(60, 30))))

def parse_authors(raw):
    if not raw:
        return []
    raw = re.sub(r"[\[【].*?[\]】]", "", raw)
    for sep in ["/", "；", ";", "、", ","]:
        if sep in raw:
            parts = [a.strip() for a in raw.split(sep) if a.strip()]
            return parts[:4]
    return [raw.strip()][:4]


# ─── 主流程 ───────────────────────────────────────────────────────────────────

def main():
    conn = _db.connections["default"]

    # 删除上次乱码导入的记录（标志：ISBN 无短横线且书名包含 ?）
    with conn.cursor() as cur:
        cur.execute("SELECT ISBN FROM book WHERE ISBN NOT LIKE '%-%' AND Title LIKE '%?%'")
        garbled_isbns = [row[0] for row in cur.fetchall()]
    if garbled_isbns:
        placeholders = ",".join(["%s"] * len(garbled_isbns))
        with conn.cursor() as cur:
            cur.execute(f"SET FOREIGN_KEY_CHECKS=0")
            cur.execute(f"DELETE FROM bookauthor WHERE ISBN IN ({placeholders})", garbled_isbns)
            cur.execute(f"DELETE FROM book WHERE ISBN IN ({placeholders})", garbled_isbns)
            cur.execute(f"SET FOREIGN_KEY_CHECKS=1")
        conn.commit()
        print(f"已清理 {len(garbled_isbns)} 条乱码记录")

    # 查询已有 ISBN，避免重复
    with conn.cursor() as cur:
        cur.execute("SELECT ISBN FROM book")
        existing = {row[0] for row in cur.fetchall()}

    print(f"数据库已有 {len(existing)} 本书")

    book_rows   = []
    author_rows = []
    seen_isbn   = set(existing)
    skipped     = 0

    with open(INPUT_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if len(book_rows) >= MAX_BOOKS:
                break

            isbn_raw = clean(row.get("ISBM") or row.get("ISBN") or row.get("isbn"))
            if not isbn_raw or not is_valid_isbn13(isbn_raw):
                skipped += 1
                continue
            isbn = re.sub(r"\D", "", isbn_raw)
            if isbn in seen_isbn:
                skipped += 1
                continue

            title = clean(row.get("书名"))
            if not is_chinese(title):
                skipped += 1
                continue

            publisher = clean(row.get("出版社"))
            authors   = parse_authors(clean(row.get("作者")))

            seen_isbn.add(isbn)
            book_rows.append((
                isbn,
                title[:100],
                publisher[:100] if publisher else None,
                random_price(),
                None,                 # keywords（CSV 无此字段）
                cover_url(isbn),
                random_stock(),
                random.choice(LOCATIONS),
                MIN_STOCK_LIMIT,
            ))
            for order, name in enumerate(authors, start=1):
                author_rows.append((isbn, name[:50], order))

    print(f"待导入：{len(book_rows)} 本书，{len(author_rows)} 条作者  |  跳过：{skipped}")

    # 批量插入
    book_sql = (
        "INSERT IGNORE INTO `book` "
        "(`ISBN`,`Title`,`Publisher`,`Price`,`Keywords`,`CoverImage`,"
        "`StockQty`,`Location`,`MinStockLimit`) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    )
    author_sql = (
        "INSERT IGNORE INTO `bookauthor` "
        "(`ISBN`,`AuthorName`,`AuthorOrder`) VALUES (%s,%s,%s)"
    )

    with conn.cursor() as cur:
        cur.executemany(book_sql, book_rows)
        cur.executemany(author_sql, author_rows)
    conn.commit()

    # 验证
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM book")
        total_books = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM bookauthor")
        total_authors = cur.fetchone()[0]
        cur.execute("SELECT Title, Location FROM book WHERE `ISBN` NOT LIKE '978-7-%' LIMIT 3")
        samples = cur.fetchall()

    print(f"\n✅ 导入完成：共 {total_books} 本书，{total_authors} 条作者记录")
    print("示例：")
    for title, loc in samples:
        print(f"  {title}  [{loc}]")


if __name__ == "__main__":
    main()
