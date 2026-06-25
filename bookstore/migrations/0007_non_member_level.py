from django.db import migrations


def add_non_member_level(apps, schema_editor):
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO creditlevel (LevelID, DiscountRate, CanUseCredit, CreditLimit)
            SELECT 0, 1.00, 0, 0.00
            FROM DUAL
            WHERE NOT EXISTS (SELECT 1 FROM creditlevel WHERE LevelID = 0)
            """
        )
        cursor.execute(
            """
            UPDATE customer c
            LEFT JOIN customer_profile cp ON cp.customer_id = c.CustomerID
            SET c.LevelID = 0, c.CreditLimit = 0.00
            WHERE cp.member_since IS NULL OR cp.customer_id IS NULL
            """
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
            WHERE cp.member_since IS NOT NULL
            """
        )


class Migration(migrations.Migration):

    dependencies = [
        ("bookstore", "0006_seed_member_profiles"),
    ]

    operations = [
        migrations.RunPython(add_non_member_level, migrations.RunPython.noop),
    ]
