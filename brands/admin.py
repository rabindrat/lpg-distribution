from django.contrib import admin

from .models import LPGBrand


@admin.register(LPGBrand)
class LPGBrandAdmin(admin.ModelAdmin):
    list_display = ("brand_id", "name_en", "name_ne", "code", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name_en", "name_ne", "code")
    readonly_fields = ("brand_id", "created_at", "updated_at")
