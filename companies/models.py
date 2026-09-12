from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from brands.models import LPGBrand


class LPGCompany(models.Model):
    """A bottling or industry company participating in LPG distribution."""

    company_id = models.PositiveIntegerField(primary_key=True)
    code = models.SlugField(max_length=100, unique=True)
    legal_name = models.CharField(max_length=200)
    main_location = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=160)
    phone = models.CharField(max_length=120)
    email = models.EmailField(max_length=254)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["company_id"]
        verbose_name = "LPG company"
        verbose_name_plural = "LPG companies"

    def __str__(self):
        return self.legal_name


class CompanyBrand(models.Model):
    """Flexible company-to-brand link; a company may have multiple brands."""

    company = models.ForeignKey(
        LPGCompany,
        on_delete=models.PROTECT,
        related_name="brand_links",
    )
    brand = models.ForeignKey(
        LPGBrand,
        on_delete=models.PROTECT,
        related_name="company_links",
    )
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["company_id", "-is_primary", "brand_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "brand"],
                name="one_company_brand_link",
            )
        ]

    def __str__(self):
        return f"{self.company} — {self.brand}"


class CompanyMembership(models.Model):
    class Role(models.TextChoices):
        ADMIN = "admin", "Company administrator"
        SUPPLY_OPERATOR = "supply_operator", "Supply operator"
        REVIEWER = "reviewer", "Company reviewer"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="company_memberships",
    )
    company = models.ForeignKey(
        LPGCompany,
        on_delete=models.PROTECT,
        related_name="memberships",
    )
    role = models.CharField(max_length=30, choices=Role.choices)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "company"],
                name="one_company_membership_per_user",
            )
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Membership is the company scope; the group is the broad access marker.
        from django.contrib.auth.models import Group

        from .roles import COMPANY_GROUP

        group, _ = Group.objects.get_or_create(name=COMPANY_GROUP)
        self.user.groups.add(group)

    def __str__(self):
        return f"{self.user} — {self.company} ({self.get_role_display()})"


class CompanySupplyReport(models.Model):
    """Initial daily company report; the append-only ledger comes later."""

    company = models.ForeignKey(
        LPGCompany,
        on_delete=models.PROTECT,
        related_name="supply_reports",
    )
    brand = models.ForeignKey(
        LPGBrand,
        on_delete=models.PROTECT,
        related_name="company_supply_reports",
    )
    report_date = models.DateField()
    cylinders_received = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    cylinders_delivered_to_dealers = models.PositiveIntegerField(
        validators=[MinValueValidator(0)]
    )
    notes = models.TextField(blank=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="submitted_supply_reports",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-report_date", "company_id", "brand_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "brand", "report_date"],
                name="one_company_brand_supply_report_per_day",
            )
        ]

    def __str__(self):
        return f"{self.company} — {self.brand} — {self.report_date}"
