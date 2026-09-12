import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("applicants", "0001_initial"),
        ("brands", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="lpgapplication",
            name="preferred_brand",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="preferred_applications",
                to="brands.lpgbrand",
            ),
        ),
    ]
