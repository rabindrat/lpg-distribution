from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from brands.models import LPGBrand


class DealerProfile(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        PENDING_VERIFICATION = "pending_verification", "Pending Company Verification"
        CORRECTION_REQUIRED = "correction_required", "Verification Correction Required"
        PHYSICALLY_VERIFIED = "physically_verified", "Physically Verified"
        PENDING_APPROVAL = "pending_approval", "Pending Company Approval"
        ACTIVE = "active", "Company Approved / Active"
        REJECTED = "rejected", "Rejected"
        SUSPENDED = "suspended", "Suspended"
        INACTIVE = "inactive", "Inactive"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="dealer_profile",
    )
    dealer_name = models.CharField(max_length=160)
    proprietor_name = models.CharField(max_length=160)
    mobile_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField()
    municipality = models.CharField(max_length=120)
    ward = models.CharField(max_length=20)
    tole = models.CharField("Tole / street", max_length=160)
    address = models.CharField(max_length=240)
    house_plot_number = models.CharField("House / plot number", max_length=60)
    phones = models.JSONField(default=list, blank=True, encoder=DjangoJSONEncoder)
    brands = models.ManyToManyField(
        LPGBrand,
        through="DealerBrandAuthorization",
        related_name="authorized_dealers",
        blank=True,
    )
    authorization_license = models.CharField("Authorization / license number", max_length=120)
    gps_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    gps_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    shop_photo = models.FileField(upload_to="dealers/shop-photos/")
    supporting_document = models.FileField(
        upload_to="dealers/supporting-documents/",
        blank=True,
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.SUBMITTED,
    )
    verification_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="dealer_verifications",
        null=True,
        blank=True,
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="dealer_approvals",
        null=True,
        blank=True,
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        permissions = [
            ("can_verify_dealers", "Can perform physical dealer verification"),
            ("can_approve_dealers", "Can approve or reject dealers"),
        ]

    def submit(self):
        self.status = self.Status.SUBMITTED
        self.save(update_fields=["status", "updated_at"])

    def mark_pending_verification(self):
        self.status = self.Status.PENDING_VERIFICATION
        self.save(update_fields=["status", "updated_at"])

    def mark_verified(self, reviewer, notes=""):
        self.status = self.Status.PENDING_APPROVAL
        self.verified_by = reviewer
        self.verified_at = timezone.now()
        self.verification_notes = notes
        self.save(
            update_fields=[
                "status",
                "verified_by",
                "verified_at",
                "verification_notes",
                "updated_at",
            ]
        )

    def approve(self, approver):
        self.status = self.Status.ACTIVE
        self.approved_by = approver
        self.approved_at = timezone.now()
        self.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])

    def reject(self, reason=""):
        self.status = self.Status.REJECTED
        self.rejection_reason = reason
        self.save(update_fields=["status", "rejection_reason", "updated_at"])

    @property
    def display_brand(self):
        authorization = self.brand_authorizations.select_related("brand").first()
        return authorization.brand.name_en if authorization else ""

    def __str__(self):
        return self.dealer_name


class DealerBrandAuthorization(models.Model):
    """A dealer may be authorized for multiple brands from multiple companies."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        EXPIRED = "expired", "Expired"

    dealer = models.ForeignKey(
        DealerProfile,
        on_delete=models.PROTECT,
        related_name="brand_authorizations",
    )
    brand = models.ForeignKey(
        LPGBrand,
        on_delete=models.PROTECT,
        related_name="dealer_authorizations",
    )
    authorization_license = models.CharField(max_length=120, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["dealer_id", "-is_primary", "brand_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["dealer", "brand"],
                name="one_dealer_brand_authorization",
            )
        ]

    def __str__(self):
        return f"{self.dealer} — {self.brand}"


class DealerRegistry(models.Model):
    """Seeded dealer/depot directory awaiting phone-verified onboarding."""

    class Status(models.TextChoices):
        UNCLAIMED = "unclaimed", "Unclaimed"
        CLAIMED = "claimed", "Claimed"
        ONBOARDED = "onboarded", "Onboarded"
        MERGED = "merged", "Merged"

    registry_id = models.PositiveIntegerField(primary_key=True)
    brand = models.ForeignKey(
        LPGBrand,
        on_delete=models.PROTECT,
        related_name="registry_dealers",
    )
    dealer_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=160)
    phones = models.JSONField(default=list, encoder=DjangoJSONEncoder)
    address = models.CharField(max_length=240)
    district = models.CharField(max_length=120, blank=True)
    local_level = models.CharField(max_length=120, blank=True)
    ward = models.CharField(max_length=20, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UNCLAIMED,
    )
    onboarded_dealer = models.OneToOneField(
        DealerProfile,
        on_delete=models.SET_NULL,
        related_name="registry_entry",
        null=True,
        blank=True,
    )
    source = models.CharField(max_length=120, default="kathmandu-valley-dealer-directory")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["brand_id", "dealer_name", "registry_id"]
        verbose_name = "dealer directory entry"
        verbose_name_plural = "dealer directory entries"

    def __str__(self):
        return f"{self.dealer_name} ({self.brand.name_en})"
