from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import DealerRegistrationForm


def register(request):
    if request.user.is_authenticated:
        return redirect("dealer-dashboard") if hasattr(request.user, "dealer_profile") else redirect("dashboard")
    form = DealerRegistrationForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        dealer = form.save()
        login(request, dealer.user)
        messages.success(
            request,
            "Dealer registration submitted. The LPG company must verify and approve it before activation.",
        )
        return redirect("dealer-dashboard")
    return render(request, "dealers/register.html", {"form": form})


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect("login")
    dealer = getattr(request.user, "dealer_profile", None)
    if dealer is None:
        return redirect("dealer-register")
    return render(request, "dealers/dashboard.html", {"dealer": dealer})
