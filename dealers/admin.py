from django.contrib import admin, messages

from .models import DealerBrandAuthorization, DealerProfile, DealerRegistry


class DealerBrandAuthorizationInline(admin.TabularInline):
    model = DealerBrandAuthorization
    extra = 0


@admin.action(description="Move selected dealers to pending verification")
def mark_pending_verification(modeladmin, request, queryset):
    updated = queryset.filter(status=DealerProfile.Status.SUBMITTED).update(
        status=DealerProfile.Status.PENDING_VERIFICATION
    )
    modeladmin.message_user(request, f"{updated} dealer(s) queued for verification.", messages.SUCCESS)


@admin.action(description="Approve selected verified dealers")
def approve_dealers(modeladmin, request, queryset):
    updated = 0
    for dealer in queryset.filter(status=DealerProfile.Status.PENDING_APPROVAL):
        dealer.approve(request.user)
        updated += 1
    modeladmin.message_user(request, f"{updated} dealer(s) activated.", messages.SUCCESS)


@admin.action(description="Mark selected dealers physically verified")
def mark_physically_verified(modeladmin, request, queryset):
    updated = 0
    for dealer in queryset.filter(
        status__in=[
            DealerProfile.Status.PENDING_VERIFICATION,
            DealerProfile.Status.PHYSICALLY_VERIFIED,
        ]
    ):
        dealer.mark_verified(request.user, notes="Marked verified through administrative review.")
        updated += 1
    modeladmin.message_user(request, f"{updated} dealer(s) moved to pending approval.", messages.SUCCESS)


@admin.action(description="Reject selected dealers")
def reject_dealers(modeladmin, request, queryset):
    updated = queryset.exclude(status=DealerProfile.Status.ACTIVE).update(
        status=DealerProfile.Status.REJECTED,
        rejection_reason="Rejected through administrative review.",
    )
    modeladmin.message_user(request, f"{updated} dealer(s) rejected.", messages.WARNING)


@admin.register(DealerProfile)
class DealerProfileAdmin(admin.ModelAdmin):
    list_display = (
        "dealer_name",
        "proprietor_name",
        "municipality",
        "display_brand",
        "status",
        "created_at",
    )
    list_filter = ("status", "municipality", "brand_authorizations__brand")
    search_fields = (
        "dealer_name",
        "proprietor_name",
        "mobile_number",
        "authorization_license",
        "brand_authorizations__brand__name_en",
    )
    readonly_fields = (
        "user",
        "created_at",
        "updated_at",
        "verified_by",
        "verified_at",
        "approved_by",
        "approved_at",
    )
    actions = [mark_pending_verification, mark_physically_verified, approve_dealers, reject_dealers]
    inlines = [DealerBrandAuthorizationInline]


@admin.register(DealerBrandAuthorization)
class DealerBrandAuthorizationAdmin(admin.ModelAdmin):
    list_display = ("dealer", "brand", "status", "is_primary")
    list_filter = ("status", "is_primary", "brand")
    search_fields = ("dealer__dealer_name", "brand__name_en", "brand__code")


@admin.register(DealerRegistry)
class DealerRegistryAdmin(admin.ModelAdmin):
    list_display = (
        "registry_id",
        "dealer_name",
        "brand",
        "district",
        "local_level",
        "status",
        "onboarded_dealer",
    )
    list_filter = ("status", "brand", "district", "local_level")
    search_fields = ("dealer_name", "contact_person", "address", "phones")
    readonly_fields = ("registry_id", "created_at", "updated_at")
