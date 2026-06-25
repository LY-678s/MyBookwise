from django.db import migrations


def seed_and_repair_profiles(apps, schema_editor):
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO customer_profile (customer_id, points, member_since, updated_at)
            SELECT c.CustomerID, 0, NULL, NOW(6)
            FROM customer c
            WHERE NOT EXISTS (
                SELECT 1 FROM customer_profile cp WHERE cp.customer_id = c.CustomerID
            )
            """
        )

        demos = [
            (2, 5500, "2025-12-19 16:45:13"),
            (3, 10000, "2025-12-19 16:45:13"),
            (4, 1200, "2025-12-19 16:45:13"),
            (5, 2500, "2025-12-19 16:45:13"),
        ]
        for cid, points, since in demos:
            cursor.execute(
                """
                INSERT INTO customer_profile (customer_id, points, member_since, updated_at)
                VALUES (%s, %s, %s, NOW(6))
                ON DUPLICATE KEY UPDATE
                    points = VALUES(points),
                    member_since = VALUES(member_since),
                    updated_at = NOW(6)
                """,
                [cid, points, since],
            )

        cursor.execute(
            "UPDATE customer_profile SET points = 0 WHERE member_since IS NULL AND points <> 0"
        )

        cursor.execute(
            """
            UPDATE customer c
            JOIN customer_profile cp ON cp.customer_id = c.CustomerID
            JOIN creditlevel cl ON cl.LevelID = (
                CASE
                    WHEN cp.points >= 10000 THEN 5
                    WHEN cp.points >= 5000 THEN 4
                    WHEN cp.points >= 2000 THEN 3
                    WHEN cp.points >= 1000 THEN 2
                    ELSE 1
                END
            )
            SET c.LevelID = cl.LevelID, c.CreditLimit = cl.CreditLimit
            """
        )


class Migration(migrations.Migration):

    dependencies = [
        ("bookstore", "0005_drop_balance_member_schema"),
    ]

    operations = [
        migrations.RunPython(seed_and_repair_profiles, migrations.RunPython.noop),
    ]
