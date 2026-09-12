from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render

from .forms import ApplicantRegistrationForm, HouseholdForm, LPGApplicationForm
from .models import ApplicantProfile, Household, LPGApplication


def home(request):
    if request.user.is_authenticated:
        if getattr(request.user, "dealer_profile", None):
            return redirect("dealer-dashboard")
        return redirect("dashboard")
    return render(request, "home.html")


def user_login(request):
    if request.user.is_authenticated:
        return home(request)
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        next_url = request.POST.get("next")
        if next_url:
            return redirect(next_url)
        if getattr(user, "dealer_profile", None):
            return redirect("dealer-dashboard")
        return redirect("dashboard")
    return render(request, "registration/login.html", {"form": form, "next": request.GET.get("next")})


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = ApplicantRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Your account was created. Add your household details to continue.")
        return redirect("household")
    return render(request, "registration/register.html", {"form": form})


@login_required
def household(request):
    profile, _ = ApplicantProfile.objects.get_or_create(
        user=request.user,
        defaults={"mobile_number": request.user.username},
    )
    instance = profile.household
    form = HouseholdForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        household_record = form.save(commit=False)
        household_record.created_by = request.user
        household_record.save()
        profile.household = household_record
        profile.save(update_fields=["household"])
        messages.success(request, "Household details saved.")
        return redirect("apply")
    return render(request, "applicants/household_form.html", {"form": form, "household": instance})


@login_required
def apply(request):
    profile = ApplicantProfile.objects.filter(user=request.user).select_related("household").first()
    household_record = profile.household if profile else None
    if not household_record:
        messages.info(request, "Add your household details before applying.")
        return redirect("household")
    form = LPGApplicationForm(request.POST or None, household=household_record)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                application = form.save(commit=False)
                application.applicant = request.user
                application.household = household_record
                application.save()
        except IntegrityError:
            form.add_error(None, "This household already has an application for the current month.")
        else:
            messages.success(request, f"Application {application.reference} submitted.")
            return redirect("dashboard")
    return render(request, "applicants/application_form.html", {"form": form, "household": household_record})


@login_required
def dashboard(request):
    profile = ApplicantProfile.objects.filter(user=request.user).select_related("household").first()
    household_record = profile.household if profile else None
    applications = (
        LPGApplication.objects.filter(household=household_record)
        if household_record
        else LPGApplication.objects.none()
    )
    return render(
        request,
        "applicants/dashboard.html",
        {"profile": profile, "household": household_record, "applications": applications},
    )
