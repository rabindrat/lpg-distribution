import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from brands.models import LPGBrand
from dealers.models import DealerProfile


class CylinderUnit(models.Model):
    """The reusable physical cylinder identified across refill cycles."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        DAMAGED = "damaged", "Damaged"
        RETIRED = "retired", "Retired"

    dealer = models.ForeignKey(
        DealerProfile,
        on_delete=models.PROTECT,
        related_name="cylinder_units",
    )
    brand = models.ForeignKey(
        LPGBrand,
        on_delete=models.PROTECT,
        related_name="cylinder_units",
    )
    asset_code = models.CharField(max_length=32, unique=True, editable=False)
    manufacturer_serial_number = models.CharField(
        max_length=120,
        unique=True,
        null=True,
        blank=True,
    )
    capacity_kg = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["asset_code"]

    def save(self, *args, **kwargs):
        if not self.asset_code:
            self.asset_code = f"CYL-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.manufacturer_serial_number or self.asset_code


class CylinderFill(models.Model):
    """One filled inventory cycle for a reusable cylinder unit."""

    class Status(models.TextChoices):
        IN_STOCK = "in_stock", "In dealer stock"
        RESERVED = "reserved", "Reserved"
        SOLD_PENDING_RECEIPT = "sold_pending_receipt", "Sold, receipt pending"
        RECEIPT_CONFIRMED = "receipt_confirmed", "Receipt confirmed"
        RETURNED_EMPTY = "returned_empty", "Returned empty"
        DAMAGED = "damaged", "Damaged"
        CANCELLED = "cancelled", "Cancelled"

    cylinder_unit = models.ForeignKey(
        CylinderUnit,
        on_delete=models.PROTECT,
        related_name="fills",
    )
    dealer = models.ForeignKey(
        DealerProfile,
        on_delete=models.PROTECT,
        related_name="cylinder_fills",
    )
    brand = models.ForeignKey(
        LPGBrand,
        on_delete=models.PROTECT,
        related_name="cylinder_fills",
    )
    fill_reference = models.CharField(max_length=32, unique=True, editable=False)
    source_reference = models.CharField(max_length=120, blank=True)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="received_cylinder_fills",
    )
    filled_at = models.DateTimeField()
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.IN_STOCK,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["filled_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["cylinder_unit", "filled_at"],
                name="one_fill_event_per_cylinder_timestamp",
            )
        ]

    def save(self, *args, **kwargs):
        if not self.fill_reference:
            self.fill_reference = f"FILL-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.fill_reference
