from django.contrib import admin

from .models import CylinderFill, CylinderUnit


@admin.register(CylinderUnit)
class CylinderUnitAdmin(admin.ModelAdmin):
    list_display = (
        "asset_code",
        "manufacturer_serial_number",
        "dealer",
        "brand",
        "capacity_kg",
        "status",
    )
    list_filter = ("status", "brand", "dealer")
    search_fields = ("asset_code", "manufacturer_serial_number", "dealer__dealer_name")
    readonly_fields = ("asset_code", "created_at", "updated_at")


@admin.register(CylinderFill)
class CylinderFillAdmin(admin.ModelAdmin):
    list_display = (
        "fill_reference",
        "cylinder_unit",
        "dealer",
        "brand",
        "filled_at",
        "status",
    )
    list_filter = ("status", "brand", "dealer")
    search_fields = ("fill_reference", "cylinder_unit__asset_code", "source_reference")
    readonly_fields = ("fill_reference", "created_at", "updated_at")
