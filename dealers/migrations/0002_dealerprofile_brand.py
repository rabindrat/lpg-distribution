import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dealers", "0001_initial"),
        ("brands", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="dealerprofile",
            name="brand",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="dealers",
                to="brands.lpgbrand",
            ),
        ),
        migrations.AlterField(
            model_name="dealerprofile",
            name="lpg_brand",
            field=models.CharField(
                blank=True,
                max_length=120,
                verbose_name="Legacy LPG brand",
            ),
        ),
    ]
