from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("dealers", "0004_dealerregistry_dealerprofile_phones"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="dealerprofile",
            name="brand",
        ),
        migrations.RemoveField(
            model_name="dealerprofile",
            name="lpg_brand",
        ),
    ]
