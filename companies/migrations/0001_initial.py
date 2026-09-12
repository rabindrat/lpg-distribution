import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("brands", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="LPGCompany",
            fields=[
                ("company_id", models.PositiveIntegerField(primary_key=True, serialize=False)),
                ("code", models.SlugField(max_length=100, unique=True)),
                ("legal_name", models.CharField(max_length=200)),
                ("main_location", models.CharField(max_length=200)),
                ("contact_person", models.CharField(max_length=160)),
                ("phone", models.CharField(max_length=120)),
                ("email", models.EmailField(max_length=254)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["company_id"],
                "verbose_name": "LPG company",
                "verbose_name_plural": "LPG companies",
            },
        ),
        migrations.CreateModel(
            name="CompanyMembership",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(choices=[("admin", "Company administrator"), ("supply_operator", "Supply operator"), ("reviewer", "Company reviewer")], max_length=30)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="memberships", to="companies.lpgcompany")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="company_memberships", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="CompanyBrand",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_primary", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("brand", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="company_links", to="brands.lpgbrand")),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="brand_links", to="companies.lpgcompany")),
            ],
            options={"ordering": ["company_id", "-is_primary", "brand_id"]},
        ),
        migrations.CreateModel(
            name="CompanySupplyReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("report_date", models.DateField()),
                ("cylinders_received", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ("cylinders_delivered_to_dealers", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("brand", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="company_supply_reports", to="brands.lpgbrand")),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="supply_reports", to="companies.lpgcompany")),
                ("submitted_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="submitted_supply_reports", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-report_date", "company_id", "brand_id"]},
        ),
        migrations.AddConstraint(
            model_name="companymembership",
            constraint=models.UniqueConstraint(fields=("user", "company"), name="one_company_membership_per_user"),
        ),
        migrations.AddConstraint(
            model_name="companybrand",
            constraint=models.UniqueConstraint(fields=("company", "brand"), name="one_company_brand_link"),
        ),
        migrations.AddConstraint(
            model_name="companysupplyreport",
            constraint=models.UniqueConstraint(fields=("company", "brand", "report_date"), name="one_company_brand_supply_report_per_day"),
        ),
    ]
