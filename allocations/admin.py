from django.contrib import admin

from .models import Allocation, AllocationRun


@admin.register(AllocationRun)
class AllocationRunAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "dealer",
        "brand",
        "requested_quantity",
        "candidate_count",
        "selected_count",
        "status",
        "created_at",
    )
    list_filter = ("status", "brand")
    search_fields = ("dealer__dealer_name", "brand__name_en")
    readonly_fields = (
        "candidate_count",
        "selected_count",
        "started_at",
        "completed_at",
        "error_message",
        "created_at",
        "updated_at",
    )


@admin.register(Allocation)
class AllocationAdmin(admin.ModelAdmin):
    list_display = (
        "application",
        "dealer",
        "brand",
        "rank",
        "priority_snapshot",
        "distance_meters",
        "status",
    )
    list_filter = ("status", "priority_snapshot", "brand")
    search_fields = (
        "application__reference",
        "dealer__dealer_name",
    )
    readonly_fields = (
        "run",
        "application",
        "dealer",
        "brand",
        "rank",
        "priority_snapshot",
        "distance_meters",
        "created_at",
        "updated_at",
    )
