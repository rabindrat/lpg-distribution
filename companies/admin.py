from django.contrib import admin

from .models import CompanyBrand, CompanyMembership, CompanySupplyReport, LPGCompany


@admin.register(CompanyBrand)
class CompanyBrandAdmin(admin.ModelAdmin):
    list_display = ("company", "brand", "is_primary", "is_active")
    list_filter = ("is_primary", "is_active", "company")
    search_fields = ("company__legal_name", "brand__name_en", "brand__code")


@admin.register(LPGCompany)
class LPGCompanyAdmin(admin.ModelAdmin):
    list_display = ("company_id", "legal_name", "main_location", "is_active")
    list_filter = ("is_active",)
    search_fields = ("legal_name", "code", "main_location", "contact_person")
    readonly_fields = ("company_id", "created_at", "updated_at")


@admin.register(CompanyMembership)
class CompanyMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "company", "role", "is_active")
    list_filter = ("role", "is_active", "company")
    search_fields = ("user__username", "user__email", "company__legal_name")


@admin.register(CompanySupplyReport)
class CompanySupplyReportAdmin(admin.ModelAdmin):
    list_display = (
        "report_date",
        "company",
        "brand",
        "cylinders_received",
        "cylinders_delivered_to_dealers",
        "submitted_by",
    )
    list_filter = ("company", "brand", "report_date")
    search_fields = ("company__legal_name", "brand__name_en", "submitted_by__username")
    readonly_fields = ("created_at", "updated_at")
