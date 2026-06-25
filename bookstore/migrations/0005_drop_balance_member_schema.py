from django.db import migrations


def apply_member_schema(apps, schema_editor):
    from django.db import connection

    with connection.cursor() as cursor:
        rows = [
            (1, 0.95, 1, 300),
            (2, 0.93, 1, 800),
            (3, 0.90, 1, 1500),
            (4, 0.88, 1, 3000),
            (5, 0.85, 1, 8000),
        ]
        for level_id, rate, can_use, limit in rows:
            cursor.execute(
                """
                UPDATE creditlevel
                SET DiscountRate=%s, CanUseCredit=%s, CreditLimit=%s
                WHERE LevelID=%s
                """,
                [rate, can_use, limit, level_id],
            )

        cursor.execute(
            """
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'customer'
              AND COLUMN_NAME = 'Balance'
            """
        )
        if cursor.fetchone()[0]:
            cursor.execute("ALTER TABLE customer DROP CHECK CK_Customer_Balance")
        cursor.execute(
            """
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'customer'
              AND COLUMN_NAME = 'TotalSpent'
            """
        )
        if cursor.fetchone()[0]:
            cursor.execute("ALTER TABLE customer DROP CHECK customer_chk_1")

        for col in ("Balance", "TotalSpent"):
            cursor.execute(
                """
                SELECT COUNT(*) FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'customer'
                  AND COLUMN_NAME = %s
                """,
                [col],
            )
            if cursor.fetchone()[0]:
                cursor.execute(f"ALTER TABLE customer DROP COLUMN `{col}`")


class Migration(migrations.Migration):

    dependencies = [
        ("bookstore", "0004_member_level_rates"),
    ]

    operations = [
        migrations.RunPython(apply_member_schema, migrations.RunPython.noop),
    ]
