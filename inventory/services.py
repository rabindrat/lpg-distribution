from django.db import transaction
from django.utils import timezone

from .models import CylinderFill, CylinderUnit


@transaction.atomic
def receive_cylinder_batch(*, dealer, brand, quantity, created_by, source_reference=""):
    """Register individually identifiable cylinders and their current fill cycle."""

    now = timezone.now()
    fills = []
    for _ in range(quantity):
        unit = CylinderUnit.objects.create(dealer=dealer, brand=brand)
        fills.append(
            CylinderFill.objects.create(
                cylinder_unit=unit,
                dealer=dealer,
                brand=brand,
                received_by=created_by,
                filled_at=now,
                source_reference=source_reference,
            )
        )
    return fills
