from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("bookstore", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CustomerProfile",
            fields=[
                (
                    "customer",
                    models.OneToOneField(
                        db_column="customer_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        related_name="profile",
                        serialize=False,
                        to="bookstore.customer",
                    ),
                ),
                ("points", models.IntegerField(default=0)),
                ("membership_expires_at", models.DateTimeField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "会员档案",
                "verbose_name_plural": "会员档案",
                "db_table": "customer_profile",
            },
        ),
        migrations.CreateModel(
            name="StripePaymentRecord",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("session_id", models.CharField(max_length=255, unique=True)),
                ("amount_cents", models.IntegerField()),
                ("currency", models.CharField(default="cny", max_length=8)),
                ("purpose", models.CharField(default="membership", max_length=32)),
                ("status", models.CharField(default="pending", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("paid_at", models.DateTimeField(blank=True, null=True)),
                (
                    "customer",
                    models.ForeignKey(
                        db_column="customer_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="bookstore.customer",
                    ),
                ),
            ],
            options={
                "verbose_name": "Stripe 支付记录",
                "verbose_name_plural": "Stripe 支付记录",
                "db_table": "stripe_payment_record",
            },
        ),
    ]
