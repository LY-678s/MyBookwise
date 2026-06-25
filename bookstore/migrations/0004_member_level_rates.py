from django.db import migrations


def update_member_levels(apps, schema_editor):
    from django.db import connection

    rows = [
        (1, 0.95, 1, 300),
        (2, 0.93, 1, 800),
        (3, 0.90, 1, 1500),
        (4, 0.88, 1, 3000),
        (5, 0.85, 1, 8000),
    ]
    with connection.cursor() as cursor:
        for level_id, rate, can_use, limit in rows:
            cursor.execute(
                """
                UPDATE creditlevel
                SET DiscountRate=%s, CanUseCredit=%s, CreditLimit=%s
                WHERE LevelID=%s
                """,
                [rate, can_use, limit, level_id],
            )


class Migration(migrations.Migration):

    dependencies = [
        ("bookstore", "0003_member_reading_pass"),
    ]

    operations = [
        migrations.RunPython(update_member_levels, migrations.RunPython.noop),
    ]
