from math import asin, cos, radians, sin, sqrt

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from applicants.models import LPGApplication
from dealers.models import DealerBrandAuthorization

from .models import Allocation, AllocationRun


def queue_allocation_run(*, dealer, brand, requested_quantity, created_by):
    """Persist a run and enqueue it only after the database commit succeeds."""

    with transaction.atomic():
        run = AllocationRun.objects.create(
            dealer=dealer,
            brand=brand,
            requested_quantity=requested_quantity,
            created_by=created_by,
        )
        from .tasks import run_allocation

        transaction.on_commit(lambda: run_allocation.delay(run.pk))
    return run


def haversine_distance_meters(lat1, lon1, lat2, lon2):
    """Return the great-circle distance between two coordinate pairs."""

    earth_radius_m = 6_371_000
    lat1, lon1, lat2, lon2 = map(
        radians, (float(lat1), float(lon1), float(lat2), float(lon2))
    )
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    value = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    return 2 * earth_radius_m * asin(sqrt(value))


def _distance_for_application(application, dealer):
    household = application.household
    if None in (
        household.latitude,
        household.longitude,
        dealer.gps_latitude,
        dealer.gps_longitude,
    ):
        return None
    return haversine_distance_meters(
        household.latitude,
        household.longitude,
        dealer.gps_latitude,
        dealer.gps_longitude,
    )


def _candidate_sort_key(item):
    application, distance = item
    priority_rank = 0 if application.priority == "P1" else 1
    return (
        priority_rank,
        distance if distance is not None else float("inf"),
        application.created_at,
        application.pk,
    )


@transaction.atomic
def execute_allocation_run(run_id):
    """Select and reserve applicants for a run in one database transaction."""

    run = (
        AllocationRun.objects.select_for_update()
        .select_related("dealer", "brand")
        .get(pk=run_id)
    )
    if run.status == AllocationRun.Status.COMPLETED:
        return {
            "run_id": run.pk,
            "status": run.status,
            "selected_count": run.selected_count,
        }
    if run.status != AllocationRun.Status.QUEUED:
        return {"run_id": run.pk, "status": run.status, "selected_count": 0}
    if run.dealer.status != run.dealer.Status.ACTIVE:
        raise ValueError("Allocation requires an active dealer")
    if not run.dealer.brand_authorizations.filter(
        brand_id=run.brand_id,
        status=DealerBrandAuthorization.Status.ACTIVE,
    ).exists():
        raise ValueError("Allocation requires an active dealer brand authorization")
    run.status = AllocationRun.Status.RUNNING
    run.started_at = timezone.now()
    run.error_message = ""
    run.save(update_fields=["status", "started_at", "error_message", "updated_at"])

    applications = list(
        LPGApplication.objects.select_for_update()
        .select_related("household")
        .filter(
            Q(preferred_brand__isnull=True) | Q(preferred_brand_id=run.brand_id),
            status__in=[
                LPGApplication.Status.SUBMITTED,
                LPGApplication.Status.UNDER_REVIEW,
            ],
            allocation__isnull=True,
        )
        .order_by("created_at", "pk")
    )
    ranked = [
        (application, _distance_for_application(application, run.dealer))
        for application in applications
    ]
    ranked.sort(key=_candidate_sort_key)

    run.candidate_count = len(ranked)
    selected = ranked[: run.requested_quantity]
    for rank, (application, distance) in enumerate(selected, start=1):
        Allocation.objects.create(
            run=run,
            application=application,
            dealer=run.dealer,
            brand=run.brand,
            rank=rank,
            priority_snapshot=application.priority,
            distance_meters=round(distance, 3) if distance is not None else None,
        )
        application.status = LPGApplication.Status.ALLOCATED
        application.save(update_fields=["status", "updated_at"])

    run.status = AllocationRun.Status.COMPLETED
    run.selected_count = len(selected)
    run.completed_at = timezone.now()
    run.save(
        update_fields=[
            "status",
            "candidate_count",
            "selected_count",
            "completed_at",
            "updated_at",
        ]
    )
    return {
        "run_id": run.pk,
        "status": run.status,
        "candidate_count": run.candidate_count,
        "selected_count": run.selected_count,
    }
