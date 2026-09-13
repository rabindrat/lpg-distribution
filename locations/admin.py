from django.contrib import admin

from .models import LocationUnit


@admin.register(LocationUnit)
class LocationUnitAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "level",
        "name_en",
        "district_name",
        "is_kathmandu_valley",
        "is_active",
    )
    list_filter = ("level", "district_name", "is_kathmandu_valley", "is_active")
    search_fields = ("code", "name_en", "name_ne", "normalized_name")
    readonly_fields = ("created_at", "updated_at")
