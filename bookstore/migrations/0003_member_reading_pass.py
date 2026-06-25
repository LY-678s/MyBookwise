from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bookstore", "0002_membership_stripe"),
    ]

    operations = [
        migrations.AddField(
            model_name="customerprofile",
            name="member_since",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="customerprofile",
            name="reading_pass_expires_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
