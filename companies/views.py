from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import redirect, render

from .forms import CompanySupplyReportForm
from .models import CompanyMembership, CompanySupplyReport


@login_required
def dashboard(request):
    memberships = CompanyMembership.objects.filter(
        user=request.user,
        is_active=True,
        company__is_active=True,
    ).select_related("company")
    company_ids = memberships.values_list("company_id", flat=True)
    reports = CompanySupplyReport.objects.filter(
        company_id__in=company_ids
    ).select_related("company", "brand")
    form = CompanySupplyReportForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        report = form.save(commit=False)
        report.submitted_by = request.user
        report.save()
        return redirect("company-dashboard")

    totals = reports.aggregate(
        cylinders_received=Sum("cylinders_received"),
        cylinders_delivered_to_dealers=Sum("cylinders_delivered_to_dealers"),
    )
    return render(
        request,
        "companies/dashboard.html",
        {
            "memberships": memberships,
            "reports": reports[:20],
            "form": form,
            "totals": totals,
        },
    )
