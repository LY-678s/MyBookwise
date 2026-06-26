from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bookstore", "0007_non_member_level"),
    ]

    operations = [
        migrations.CreateModel(
            name="CartItem",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("customer_id", models.IntegerField(db_index=True)),
                ("isbn", models.CharField(max_length=20)),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "购物车项",
                "verbose_name_plural": "购物车项",
                "db_table": "cart_item",
                "unique_together": {("customer_id", "isbn")},
            },
        ),
        migrations.AddIndex(
            model_name="cartitem",
            index=models.Index(fields=["customer_id"], name="cart_item_customer_idx"),
        ),
    ]
