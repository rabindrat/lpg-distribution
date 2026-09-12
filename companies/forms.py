from django import forms

from brands.models import LPGBrand

from .models import CompanyBrand, CompanyMembership, CompanySupplyReport, LPGCompany


class CompanySupplyReportForm(forms.ModelForm):
    class Meta:
        model = CompanySupplyReport
        fields = [
            "company",
            "brand",
            "report_date",
            "cylinders_received",
            "cylinders_delivered_to_dealers",
            "notes",
        ]
        widgets = {"report_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, user, **kwargs):
        self.membership_company_ids = list(
            CompanyMembership.objects.filter(
                user=user, is_active=True, company__is_active=True
            ).values_list("company_id", flat=True)
        )
        super().__init__(*args, **kwargs)
        self.fields["company"].queryset = LPGCompany.objects.filter(
            company_id__in=self.membership_company_ids
        )
        self.fields["brand"].queryset = LPGBrand.objects.filter(
            company_links__company_id__in=self.membership_company_ids,
            company_links__is_active=True,
            is_active=True,
        ).distinct().order_by("brand_id")

    def clean(self):
        cleaned = super().clean()
        company = cleaned.get("company")
        brand = cleaned.get("brand")
        if company and brand and not CompanyBrand.objects.filter(
            company=company, brand=brand, is_active=True
        ).exists():
            self.add_error("brand", "Select a brand linked to the selected company.")
        return cleaned
