from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from allocations.services import queue_allocation_run
from inventory.models import CylinderFill
from inventory.services import receive_cylinder_batch

from .forms import CylinderReceiptForm, DealerAllocationRunForm, DealerRegistrationForm
from .models import DealerProfile, DealerRegistry


def register(request):
    if request.user.is_authenticated:
        return redirect("dealer-dashboard") if hasattr(request.user, "dealer_profile") else redirect("dashboard")
    form = DealerRegistrationForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            dealer = form.save()
        login(request, dealer.user)
        messages.success(
            request,
            "Dealer registration submitted. The LPG company must verify and approve it before activation.",
        )
        return redirect("dealer-dashboard")
    registry_data = [
        {
            "id": entry.registry_id,
            "dealer_name": entry.dealer_name,
            "contact_person": entry.contact_person,
            "phones": entry.phones,
            "address": entry.address,
            "district": entry.district,
            "local_level": entry.local_level,
            "ward": entry.ward,
            "brand_id": entry.brand_id,
        }
        for entry in DealerRegistry.objects.filter(
            status=DealerRegistry.Status.UNCLAIMED
        ).select_related("brand")
    ]
    return render(request, "dealers/register.html", {"form": form, "registry_data": registry_data})


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect("login")
    dealer = getattr(request.user, "dealer_profile", None)
    if dealer is None:
        return redirect("dealer-register")
    runs = dealer.allocation_runs.select_related("brand").all()[:10]
    stock_summary = (
        CylinderFill.objects.filter(
            dealer=dealer,
            status=CylinderFill.Status.IN_STOCK,
        )
        .values("brand__name_en")
        .annotate(count=Count("id"))
        .order_by("brand__name_en")
    )
    return render(
        request,
        "dealers/dashboard.html",
        {"dealer": dealer, "runs": runs, "stock_summary": stock_summary},
    )


@login_required
def receive_cylinders(request):
    dealer = get_object_or_404(DealerProfile, user=request.user)
    if dealer.status != DealerProfile.Status.ACTIVE:
        return HttpResponseForbidden("Only active dealers can receive stock.")
    form = CylinderReceiptForm(request.POST or None, dealer=dealer)
    if request.method == "POST" and form.is_valid():
        fills = receive_cylinder_batch(
            dealer=dealer,
            brand=form.cleaned_data["brand"],
            quantity=form.cleaned_data["quantity"],
            created_by=request.user,
            source_reference=form.cleaned_data["source_reference"],
        )
        messages.success(
            request,
            f"Recorded {len(fills)} filled cylinder(s) in dealer stock.",
        )
        return redirect("dealer-dashboard")
    return render(
        request,
        "dealers/cylinder_receipt_form.html",
        {"dealer": dealer, "form": form},
    )


@login_required
def create_allocation_run(request):
    dealer = get_object_or_404(DealerProfile, user=request.user)
    if dealer.status != DealerProfile.Status.ACTIVE:
        return HttpResponseForbidden("Only active dealers can create allocation runs.")
    form = DealerAllocationRunForm(request.POST or None, dealer=dealer)
    if request.method == "POST" and form.is_valid():
        try:
            run = queue_allocation_run(
                dealer=dealer,
                brand=form.cleaned_data["brand"],
                requested_quantity=form.cleaned_data["requested_quantity"],
                created_by=request.user,
            )
        except Exception:
            messages.error(
                request,
                "The allocation run was saved but could not be queued. Please retry it from admin.",
            )
        else:
            messages.success(
                request,
                f"Allocation run {run.pk} queued for background processing.",
            )
        return redirect("dealer-dashboard")
    return render(
        request,
        "dealers/allocation_form.html",
        {"dealer": dealer, "form": form},
    )
