import django.db.models.deletion
import django.core.serializers.json
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("brands", "0001_initial"),
        ("dealers", "0003_dealerbrandauthorization_dealerprofile_brands"),
    ]

    operations = [
        migrations.AddField(
            model_name="dealerprofile",
            name="phones",
            field=models.JSONField(blank=True, default=list, encoder=django.core.serializers.json.DjangoJSONEncoder),
        ),
        migrations.CreateModel(
            name="DealerRegistry",
            fields=[
                ("registry_id", models.PositiveIntegerField(primary_key=True, serialize=False)),
                ("dealer_name", models.CharField(max_length=200)),
                ("contact_person", models.CharField(max_length=160)),
                ("phones", models.JSONField(default=list, encoder=django.core.serializers.json.DjangoJSONEncoder)),
                ("address", models.CharField(max_length=240)),
                ("district", models.CharField(blank=True, max_length=120)),
                ("local_level", models.CharField(blank=True, max_length=120)),
                ("ward", models.CharField(blank=True, max_length=20)),
                ("status", models.CharField(choices=[("unclaimed", "Unclaimed"), ("claimed", "Claimed"), ("onboarded", "Onboarded"), ("merged", "Merged")], default="unclaimed", max_length=20)),
                ("source", models.CharField(default="kathmandu-valley-dealer-directory", max_length=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("brand", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="registry_dealers", to="brands.lpgbrand")),
                ("onboarded_dealer", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="registry_entry", to="dealers.dealerprofile")),
            ],
            options={
                "ordering": ["brand_id", "dealer_name", "registry_id"],
                "verbose_name": "dealer directory entry",
                "verbose_name_plural": "dealer directory entries",
            },
        ),
    ]
