from django.contrib import admin

from .models import LocationAlias, LocationUnit


class LocationAliasInline(admin.TabularInline):
    model = LocationAlias
    extra = 0


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
    inlines = [LocationAliasInline]


@admin.register(LocationAlias)
class LocationAliasAdmin(admin.ModelAdmin):
    list_display = ("alias", "location", "source", "is_active")
    list_filter = ("is_active", "source")
    search_fields = ("alias", "normalized_alias", "location__name_en")
    readonly_fields = ("normalized_alias", "created_at", "updated_at")
