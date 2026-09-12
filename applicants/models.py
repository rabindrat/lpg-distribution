import uuid
from datetime import date, timedelta

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from brands.models import LPGBrand


def current_month_start():
    today = timezone.localdate()
    return date(today.year, today.month, 1)


class ApplicantProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="applicant_profile",
    )
    mobile_number = models.CharField(max_length=20, unique=True)
    mobile_verified = models.BooleanField(default=False)
    household = models.ForeignKey(
        "Household",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="applicant_profiles",
    )

    def __str__(self):
        return self.user.get_full_name() or self.mobile_number


class Household(models.Model):
    municipality = models.CharField(max_length=120)
    ward = models.CharField(max_length=20)
    tole = models.CharField("Tole / street", max_length=160)
    house_number = models.CharField(max_length=40)
    flat_unit = models.CharField("Flat / unit number", max_length=40, blank=True)
    family_size = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    members = models.TextField(
        blank=True,
        help_text="Optional for the MVP; add household members one per line when needed for verification.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_households",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["municipality", "ward", "tole", "house_number"]

    def __str__(self):
        unit = f", {self.flat_unit}" if self.flat_unit else ""
        return f"{self.municipality}, Ward {self.ward}, {self.house_number}{unit}"


class LPGApplication(models.Model):
    class Category(models.TextChoices):
        LABOURER = "labourer", "Labourer"
        STUDENT = "student", "Student"
        HOUSEHOLD = "household", "Individual / Family / Household"

    class BrandPreference(models.TextChoices):
        ANY = "any", "Any available brand"
        SPECIFIC = "specific", "Prefer a specific brand"

    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        UNDER_REVIEW = "under_review", "Under review"
        ALLOCATED = "allocated", "Allocated"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"
        REJECTED = "rejected", "Rejected"

    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="lpg_applications",
    )
    household = models.ForeignKey(
        Household,
        on_delete=models.PROTECT,
        related_name="applications",
    )
    reference = models.CharField(max_length=24, unique=True, editable=False)
    category = models.CharField(max_length=20, choices=Category.choices)
    brand_preference = models.CharField(
        max_length=20,
        choices=BrandPreference.choices,
        default=BrandPreference.ANY,
    )
    preferred_brand = models.ForeignKey(
        LPGBrand,
        on_delete=models.PROTECT,
        related_name="preferred_applications",
        null=True,
        blank=True,
    )
    # Kept for compatibility with records created before the brand catalog existed.
    preferred_brand_name = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SUBMITTED,
    )
    priority = models.CharField(max_length=2, editable=False)
    due_date = models.DateField(editable=False)
    entitlement_month = models.DateField(default=current_month_start, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["household", "entitlement_month"],
                name="one_lpg_application_per_household_month",
            )
        ]

    def save(self, *args, **kwargs):
        self.entitlement_month = current_month_start()
        self.priority = (
            "P1"
            if self.category in {self.Category.LABOURER, self.Category.STUDENT}
            else "P2"
        )
        self.due_date = timezone.localdate() + timedelta(
            days=2 if self.priority == "P1" else 5
        )
        if not self.reference:
            self.reference = f"APP-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.reference
