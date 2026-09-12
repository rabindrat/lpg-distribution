from datetime import date

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from brands.models import LPGBrand

from .models import CompanyBrand, CompanyMembership, CompanySupplyReport, LPGCompany

User = get_user_model()


class CompanyCatalogTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_brands", verbosity=0)
        call_command("seed_companies", verbosity=0)

    def test_company_catalog_and_flexible_brand_links_are_seeded(self):
        self.assertEqual(LPGCompany.objects.count(), 18)
        company = LPGCompany.objects.get(company_id=15)
        self.assertEqual(company.legal_name, "Ugrachandi Gas Udhyog Pvt. Ltd.")
        self.assertEqual(company.brand_links.get(is_primary=True).brand_id, 21)

        CompanyBrand.objects.create(
            company=company,
            brand=LPGBrand.objects.get(brand_id=52),
            is_primary=False,
        )
        self.assertEqual(company.brand_links.count(), 2)

    def test_company_member_can_submit_supply_report(self):
        user = User.objects.create_user(username="company-user", password="password")
        company = LPGCompany.objects.get(company_id=1)
        brand = company.brand_links.get(is_primary=True).brand
        CompanyMembership.objects.create(
            user=user,
            company=company,
            role=CompanyMembership.Role.SUPPLY_OPERATOR,
        )
        self.assertTrue(user.groups.filter(name="Companies").exists())
        self.client.force_login(user)
        response = self.client.post(
            reverse("company-dashboard"),
            {
                "company": company.company_id,
                "brand": brand.brand_id,
                "report_date": date.today().isoformat(),
                "cylinders_received": 100,
                "cylinders_delivered_to_dealers": 80,
                "notes": "Pilot report",
            },
        )
        self.assertRedirects(response, reverse("company-dashboard"))
        report = CompanySupplyReport.objects.get(company=company, brand=brand)
        self.assertEqual(report.cylinders_received, 100)
        self.assertEqual(report.submitted_by, user)
