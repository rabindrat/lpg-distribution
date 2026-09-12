from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("applicants", "0002_lpgapplication_preferred_brand"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="lpgapplication",
            name="preferred_brand_name",
        ),
    ]
