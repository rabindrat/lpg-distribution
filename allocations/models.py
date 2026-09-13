from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from applicants.models import LPGApplication
from brands.models import LPGBrand
from dealers.models import DealerProfile


class AllocationRun(models.Model):
    """A durable request to select applicants for one dealer/brand supply."""

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    dealer = models.ForeignKey(
        DealerProfile,
        on_delete=models.PROTECT,
        related_name="allocation_runs",
    )
    brand = models.ForeignKey(
        LPGBrand,
        on_delete=models.PROTECT,
        related_name="allocation_runs",
    )
    requested_quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.QUEUED,
    )
    candidate_count = models.PositiveIntegerField(default=0)
    selected_count = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_allocation_runs",
    )
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Allocation run {self.pk} — {self.dealer} / {self.brand}"


class Allocation(models.Model):
    """A ranked applicant reservation created by an AllocationRun."""

    class Status(models.TextChoices):
        RESERVED = "reserved", "Reserved"
        SALE_RECORDED = "sale_recorded", "Sale recorded"
        RECEIPT_CONFIRMED = "receipt_confirmed", "Receipt confirmed"
        CANCELLED = "cancelled", "Cancelled"
        ESCALATED = "escalated", "Escalated"

    run = models.ForeignKey(
        AllocationRun,
        on_delete=models.PROTECT,
        related_name="allocations",
    )
    application = models.OneToOneField(
        LPGApplication,
        on_delete=models.PROTECT,
        related_name="allocation",
    )
    dealer = models.ForeignKey(
        DealerProfile,
        on_delete=models.PROTECT,
        related_name="allocations",
    )
    brand = models.ForeignKey(
        LPGBrand,
        on_delete=models.PROTECT,
        related_name="allocations",
    )
    rank = models.PositiveIntegerField()
    priority_snapshot = models.CharField(max_length=2)
    distance_meters = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=24,
        choices=Status.choices,
        default=Status.RESERVED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["rank", "pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["run", "rank"],
                name="one_allocation_rank_per_run",
            )
        ]

    def __str__(self):
        return f"{self.application.reference} — rank {self.rank}"
