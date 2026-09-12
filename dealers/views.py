from django.contrib import messages
from django.contrib.auth import login
from django.db import transaction
from django.shortcuts import redirect, render

from .forms import DealerRegistrationForm
from .models import DealerRegistry


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
    return render(request, "dealers/dashboard.html", {"dealer": dealer})
