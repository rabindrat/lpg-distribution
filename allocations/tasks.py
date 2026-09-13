from celery import shared_task
from django.utils import timezone

from .models import AllocationRun
from .services import execute_allocation_run


@shared_task(bind=True, name="allocations.run_allocation")
def run_allocation(self, run_id):
    """Run applicant selection; safe to retry after a worker interruption."""

    try:
        return execute_allocation_run(run_id)
    except Exception as exc:
        # The allocation transaction has rolled back at this point. Persist a
        # failure state separately so operators can see why a run stopped.
        AllocationRun.objects.filter(
            pk=run_id,
            status__in=[AllocationRun.Status.QUEUED, AllocationRun.Status.RUNNING],
        ).update(
            status=AllocationRun.Status.FAILED,
            error_message=str(exc),
            completed_at=timezone.now(),
        )
        raise
