from django.contrib import admin

from .models import ApplicantProfile, Complaint, Household, LPGApplication


@admin.register(ApplicantProfile)
class ApplicantProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "mobile_number", "mobile_verified", "household")
    search_fields = ("user__username", "user__first_name", "user__last_name", "mobile_number")


@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    list_display = ("municipality", "ward", "tole", "house_number", "family_size", "created_by")
    list_filter = ("municipality", "ward")
    search_fields = ("municipality", "tole", "house_number", "flat_unit")


@admin.register(LPGApplication)
class LPGApplicationAdmin(admin.ModelAdmin):
    list_display = ("reference", "household", "category", "priority", "status", "due_date")
    list_filter = ("status", "priority", "category", "entitlement_month")
    search_fields = ("reference", "applicant__username", "household__house_number")
    readonly_fields = ("reference", "priority", "due_date", "entitlement_month", "created_at", "updated_at")


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ("id", "applicant", "confirmation_number", "created_at")
    search_fields = ("confirmation_number", "complaint", "applicant__username")
    readonly_fields = ("created_at",)
