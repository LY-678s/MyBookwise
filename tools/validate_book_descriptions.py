from __future__ import annotations

import csv
import io
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SQL_PATH = ROOT / "SetDatabase" / "import_data_insert.sql"
BOOK_RE = re.compile(r"INSERT INTO book \(([^)]*)\) VALUES \((.*)\);$")


def main() -> None:
    text = SQL_PATH.read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if line.startswith("INSERT INTO book ")]
    bad_rows = []
    max_description_len = 0
    samples = []

    for index, line in enumerate(lines, start=1):
        match = BOOK_RE.match(line)
        if not match:
            bad_rows.append((index, "regex"))
            continue
        columns = [column.strip() for column in match.group(1).split(",")]
        values = next(
            csv.reader(
                io.StringIO(match.group(2)),
                delimiter=",",
                quotechar="'",
                doublequote=True,
                skipinitialspace=True,
            )
        )
        if len(columns) != len(values):
            bad_rows.append((index, len(columns), len(values)))
            continue
        if "Description" not in columns:
            bad_rows.append((index, "missing Description"))
            continue
        description = values[columns.index("Description")]
        max_description_len = max(max_description_len, len(description))
        if len(samples) < 3:
            samples.append((values[0], values[1], description))

    print(f"book lines: {len(lines)}")
    print(f"bad rows: {len(bad_rows)}")
    print(f"max description length: {max_description_len}")
    print("samples:")
    for isbn, title, description in samples:
        print(f"- {isbn} | {title} | {description}")
    if bad_rows:
        print(f"first bad rows: {bad_rows[:5]}")
        raise SystemExit(1)
    if max_description_len > 300:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
