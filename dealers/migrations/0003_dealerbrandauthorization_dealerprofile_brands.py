import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("brands", "0001_initial"),
        ("dealers", "0002_dealerprofile_brand"),
    ]

    operations = [
        migrations.CreateModel(
            name="DealerBrandAuthorization",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("authorization_license", models.CharField(blank=True, max_length=120)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("active", "Active"), ("suspended", "Suspended"), ("expired", "Expired")], default="pending", max_length=20)),
                ("is_primary", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("brand", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="dealer_authorizations", to="brands.lpgbrand")),
                ("dealer", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="brand_authorizations", to="dealers.dealerprofile")),
            ],
            options={"ordering": ["dealer_id", "-is_primary", "brand_id"]},
        ),
        migrations.AddField(
            model_name="dealerprofile",
            name="brands",
            field=models.ManyToManyField(blank=True, related_name="authorized_dealers", through="dealers.DealerBrandAuthorization", to="brands.lpgbrand"),
        ),
        migrations.AddConstraint(
            model_name="dealerbrandauthorization",
            constraint=models.UniqueConstraint(fields=("dealer", "brand"), name="one_dealer_brand_authorization"),
        ),
    ]
