from __future__ import annotations

import csv
import io
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SQL_PATH = ROOT / "SetDatabase" / "import_data_insert.sql"
ALTER_PATH = ROOT / "SetDatabase" / "add_book_description_field.sql"


BOOK_RE = re.compile(
    r"INSERT INTO book \((?P<columns>[^)]*)\) VALUES \((?P<values>.*)\);$"
)
AUTHOR_RE = re.compile(
    r"INSERT INTO bookauthor \((?P<columns>[^)]*)\) VALUES \((?P<values>.*)\);$"
)


def parse_values(values: str) -> list[str]:
    reader = csv.reader(io.StringIO(values), delimiter=",", quotechar="'", doublequote=True, skipinitialspace=True)
    return next(reader)


def sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def make_description(title: str, publisher: str, keywords: str, authors: list[str]) -> str:
    title = title.strip()
    publisher = (publisher or "未知出版社").strip()
    keyword_items = [item.strip() for item in (keywords or "").split(",") if item.strip()]
    author_text = "、".join(authors[:3]) if authors else "相关作者"
    keyword_text = "、".join(keyword_items[:4]) if keyword_items else "阅读"

    if keyword_items:
        desc = (
            f"《{title}》由{publisher}出版，作者为{author_text}。"
            f"本书围绕{keyword_text}等主题展开，适合希望拓展知识、提升阅读体验的读者。"
            f"内容兼具资料性与可读性，可作为日常阅读、课程参考或专题了解的书目。"
        )
    else:
        desc = (
            f"《{title}》由{publisher}出版，作者为{author_text}。"
            f"本书内容清晰，适合希望拓展知识面、丰富阅读选择的读者。"
            f"可用于日常阅读、课程参考或按兴趣进行专题了解。"
        )
    return desc[:300]


def main() -> None:
    text = SQL_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()

    authors_by_isbn: dict[str, list[tuple[int, str]]] = {}
    for line in lines:
        match = AUTHOR_RE.match(line)
        if not match:
            continue
        columns = [col.strip() for col in match.group("columns").split(",")]
        values = parse_values(match.group("values"))
        row = dict(zip(columns, values))
        try:
            order = int(row.get("AuthorOrder", "9999"))
        except ValueError:
            order = 9999
        authors_by_isbn.setdefault(row["ISBN"], []).append((order, row["AuthorName"]))

    authors_by_isbn = {
        isbn: [name for _, name in sorted(items)]
        for isbn, items in authors_by_isbn.items()
    }

    changed = 0
    new_lines: list[str] = []
    for line in lines:
        match = BOOK_RE.match(line)
        if not match:
            new_lines.append(line)
            continue

        columns = [col.strip() for col in match.group("columns").split(",")]
        values = parse_values(match.group("values"))
        row = dict(zip(columns, values))

        if "Description" not in columns:
            columns.append("Description")
            values.append(
                make_description(
                    row.get("Title", ""),
                    row.get("Publisher", ""),
                    row.get("Keywords", ""),
                    authors_by_isbn.get(row.get("ISBN", ""), []),
                )
            )
            changed += 1
        else:
            changed += 1

        value_sql = []
        for column, value in zip(columns, values):
            if value.upper() == "NULL":
                value_sql.append("NULL")
            elif column in {"Price", "StockQty", "MinStockLimit"}:
                value_sql.append(value)
            else:
                value_sql.append(sql_quote(value))

        new_lines.append(
            f"INSERT INTO book ({', '.join(columns)}) VALUES ({', '.join(value_sql)});"
        )

    SQL_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    ALTER_PATH.write_text(
        "ALTER TABLE book ADD COLUMN Description TEXT NULL AFTER MinStockLimit;\n",
        encoding="utf-8",
    )
    print(f"Updated {changed} book INSERT statements.")
    print(f"Wrote {ALTER_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
