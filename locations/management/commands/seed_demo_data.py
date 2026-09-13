import os
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from allocations.models import Allocation, AllocationRun
from applicants.models import ApplicantProfile, Complaint, Household, LPGApplication
from brands.models import LPGBrand
from companies.models import CompanyBrand, CompanyMembership, CompanySupplyReport, LPGCompany
from companies.roles import APPLICANT_GROUP, COMPANY_GROUP, DEALER_GROUP
from dealers.models import DealerBrandAuthorization, DealerCoverageArea, DealerProfile, DealerRegistry
from inventory.models import CylinderFill, CylinderUnit
from locations.models import LocationAlias, LocationUnit
from locations.services import normalize_location_text


User = get_user_model()


class Command(BaseCommand):
    help = "Create safe-to-rerun demo records for staging and manual workflow testing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default=os.environ.get("DEMO_DATA_PASSWORD", "DemoPass123!"),
            help="Password for newly created demo users (prefer DEMO_DATA_PASSWORD).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        password = options["password"]
        groups = self._ensure_groups()
        locations = self._seed_locations()
        brands = self._seed_brand_links()

        company_user = self._ensure_user(
            "demo-company-operator",
            "company.demo@example.com",
            "Company",
            "Operator",
            password,
            groups[COMPANY_GROUP],
        )
        company = LPGCompany.objects.get(company_id=1)
        CompanyMembership.objects.update_or_create(
            user=company_user,
            company=company,
            defaults={"role": CompanyMembership.Role.SUPPLY_OPERATOR, "is_active": True},
        )
        CompanyMembership.objects.update_or_create(
            user=company_user,
            company=LPGCompany.objects.get(company_id=2),
            defaults={"role": CompanyMembership.Role.REVIEWER, "is_active": False},
        )
        self._seed_supply_reports(company, brands["nepal_gas"], company_user)

        dealers = self._seed_dealers(password, groups[DEALER_GROUP], brands, locations)
        self._seed_registry(brands["nepal_gas"], dealers)
        applicants = self._seed_applicants(
            password,
            groups[APPLICANT_GROUP],
            brands,
            locations,
        )
        fills = self._seed_inventory(dealers["active"], brands["nepal_gas"])
        self._seed_allocations(dealers["active"], brands["nepal_gas"], applicants, fills)
        self._seed_complaints(applicants)

        self.stdout.write(self.style.SUCCESS("Staging demo data is ready (idempotent upsert)."))
        self.stdout.write(
            "Demo logins: demo-company-operator, demo-dealer-active, "
            "demo-dealer-review, demo-applicant-p1-near, demo-applicant-delivered"
        )
        self.stdout.write("Use DEMO_DATA_PASSWORD to set the password for newly created users.")

    @staticmethod
    def _ensure_groups():
        names = [APPLICANT_GROUP, COMPANY_GROUP, DEALER_GROUP]
        return {name: Group.objects.get_or_create(name=name)[0] for name in names}

    @staticmethod
    def _ensure_user(username, email, first_name, last_name, password, group):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "first_name": first_name, "last_name": last_name},
        )
        if created:
            user.set_password(password)
            user.save(update_fields=["password"])
        user.groups.add(group)
        return user

    def _seed_locations(self):
        def unit(code, level, name_en, name_ne="", parent=None, aliases=None, district="Kathmandu"):
            aliases = aliases or []
            record, _ = LocationUnit.objects.update_or_create(
                code=code,
                defaults={
                    "level": level,
                    "name_en": name_en,
                    "name_ne": name_ne,
                    "normalized_name": normalize_location_text(name_en),
                    "aliases": aliases,
                    "parent": parent,
                    "district_name": district,
                    "is_kathmandu_valley": True,
                    "is_active": True,
                },
            )
            for alias in aliases:
                LocationAlias.objects.update_or_create(
                    location=record,
                    normalized_alias=normalize_location_text(alias),
                    defaults={"alias": alias, "source": "staging-demo", "is_active": True},
                )
            return record

        kathmandu = unit(
            "DEMO-KTM-KMC",
            LocationUnit.Level.MUNICIPALITY,
            "Kathmandu Metropolitan City",
            "काठमाडौँ महानगरपालिका",
        )
        kathmandu_10 = unit(
            "DEMO-KTM-KMC-W10", LocationUnit.Level.WARD, "Ward 10", parent=kathmandu
        )
        baneshwor = unit(
            "DEMO-KTM-KMC-W10-BANESHWOR",
            LocationUnit.Level.TOLE,
            "Baneshwor",
            parent=kathmandu_10,
            aliases=["New Baneshwor", "Naya Baneshwor", "New-Baneshwar"],
        )
        lalitpur = unit(
            "DEMO-LAL-LMC",
            LocationUnit.Level.MUNICIPALITY,
            "Lalitpur Metropolitan City",
            district="Lalitpur",
        )
        lalitpur_3 = unit(
            "DEMO-LAL-LMC-W3",
            LocationUnit.Level.WARD,
            "Ward 3",
            parent=lalitpur,
            district="Lalitpur",
        )
        pulchowk = unit(
            "DEMO-LAL-LMC-W3-PULCHOWK",
            LocationUnit.Level.TOLE,
            "Pulchowk",
            parent=lalitpur_3,
            aliases=["Pulchok"],
            district="Lalitpur",
        )
        bhaktapur = unit(
            "DEMO-BHA-BMC",
            LocationUnit.Level.MUNICIPALITY,
            "Bhaktapur Municipality",
            district="Bhaktapur",
        )
        bhaktapur_5 = unit(
            "DEMO-BHA-BMC-W5",
            LocationUnit.Level.WARD,
            "Ward 5",
            parent=bhaktapur,
            district="Bhaktapur",
        )
        return {
            "kathmandu": kathmandu,
            "kathmandu_10": kathmandu_10,
            "baneshwor": baneshwor,
            "lalitpur": lalitpur,
            "lalitpur_3": lalitpur_3,
            "pulchowk": pulchowk,
            "bhaktapur": bhaktapur,
            "bhaktapur_5": bhaktapur_5,
        }

    @staticmethod
    def _seed_brand_links():
        brands = {
            "nepal_gas": LPGBrand.objects.get(brand_id=29),
            "surya_gas": LPGBrand.objects.get(brand_id=52),
        }
        CompanyBrand.objects.update_or_create(
            company_id=1,
            brand=brands["nepal_gas"],
            defaults={"is_primary": True, "is_active": True},
        )
        return brands

    @staticmethod
    def _seed_supply_reports(company, brand, submitted_by):
        today = timezone.localdate()
        for report_date, received, delivered, notes in [
            (today - timedelta(days=1), 80, 50, "Demo report: dispatch reconciled."),
            (today, 40, 0, "Demo report: supply received; dealer dispatch pending."),
        ]:
            CompanySupplyReport.objects.update_or_create(
                company=company,
                brand=brand,
                report_date=report_date,
                defaults={
                    "cylinders_received": received,
                    "cylinders_delivered_to_dealers": delivered,
                    "notes": notes,
                    "submitted_by": submitted_by,
                },
            )

    def _seed_dealers(self, password, dealer_group, brands, locations):
        specs = [
            ("active", "demo-dealer-active", "+9779800000101", "Baneshwor Demo LPG Centre", "ACTIVE", "ACTIVE", brands["nepal_gas"], "Kathmandu", "10", "Baneshwor", "27.686900", "85.342000"),
            ("review", "demo-dealer-review", "+9779800000102", "Review Queue Demo Dealer", "PENDING_VERIFICATION", "PENDING", brands["surya_gas"], "Lalitpur", "3", "Pulchowk", "27.680000", "85.316700"),
            ("correction", "demo-dealer-correction", "+9779800000103", "Correction Required Demo Dealer", "CORRECTION_REQUIRED", "PENDING", brands["nepal_gas"], "Bhaktapur", "5", "Suryabinayak", "27.671000", "85.429800"),
            ("suspended", "demo-dealer-suspended", "+9779800000104", "Suspended Demo Dealer", "SUSPENDED", "SUSPENDED", brands["nepal_gas"], "Kathmandu", "10", "Baneshwor", "27.690000", "85.345000"),
        ]
        dealers = {}
        for key, username, mobile, name, status_name, auth_status_name, brand, municipality, ward, tole, latitude, longitude in specs:
            user = self._ensure_user(
                username,
                f"{username}@example.com",
                "Demo",
                key.title(),
                password,
                dealer_group,
            )
            dealer, _ = DealerProfile.objects.update_or_create(
                user=user,
                defaults={
                    "dealer_name": name,
                    "proprietor_name": f"Demo Dealer {key.title()}",
                    "mobile_number": mobile,
                    "email": f"{username}@example.com",
                    "municipality": municipality,
                    "ward": ward,
                    "tole": tole,
                    "address": f"Demo address, {tole}",
                    "house_plot_number": "D-1",
                    "phones": [mobile.replace("+", "")],
                    "authorization_license": f"DEMO-{key.upper()}-001",
                    "gps_latitude": Decimal(latitude),
                    "gps_longitude": Decimal(longitude),
                    "shop_photo": "demo/shop-front.jpg",
                    "status": getattr(DealerProfile.Status, status_name),
                },
            )
            DealerBrandAuthorization.objects.update_or_create(
                dealer=dealer,
                brand=brand,
                defaults={
                    "authorization_license": f"DEMO-{key.upper()}-001",
                    "status": getattr(DealerBrandAuthorization.Status, auth_status_name),
                    "is_primary": True,
                },
            )
            dealers[key] = dealer

        coverage_specs = [
            (DealerCoverageArea.CoverageLevel.TOLE, "Kathmandu", "10", "Baneshwor", locations["baneshwor"]),
            (DealerCoverageArea.CoverageLevel.WARD, "Lalitpur", "3", "", locations["lalitpur_3"]),
        ]
        for level, municipality, ward, tole, location_unit in coverage_specs:
            DealerCoverageArea.objects.update_or_create(
                dealer=dealers["active"],
                coverage_level=level,
                municipality=municipality,
                ward=ward,
                tole=tole,
                defaults={"location_unit": location_unit, "created_by": dealers["active"].user, "is_active": True},
            )
        return dealers

    @staticmethod
    def _seed_registry(brand, dealers):
        rows = [
            (900001, "Unclaimed Demo LPG Dealer", DealerRegistry.Status.UNCLAIMED, None),
            (900002, "Claimed Demo LPG Dealer", DealerRegistry.Status.CLAIMED, dealers["active"]),
            (900003, "Onboarded Demo LPG Dealer", DealerRegistry.Status.ONBOARDED, dealers["review"]),
            (900004, "Merged Demo LPG Dealer", DealerRegistry.Status.MERGED, None),
        ]
        for registry_id, name, status, onboarded_dealer in rows:
            DealerRegistry.objects.update_or_create(
                registry_id=registry_id,
                defaults={
                    "brand": brand,
                    "dealer_name": name,
                    "contact_person": "Demo Contact",
                    "phones": [f"980000{registry_id}"],
                    "address": "Kathmandu Valley demo address",
                    "district": "Kathmandu",
                    "local_level": "Kathmandu Metropolitan City",
                    "ward": "10",
                    "status": status,
                    "onboarded_dealer": onboarded_dealer,
                    "source": "staging-demo",
                },
            )

    def _seed_applicants(self, password, applicant_group, brands, locations):
        specs = [
            ("p1_near", "demo-applicant-p1-near", "+9779810000201", "Labourer", LPGApplication.Category.LABOURER, LPGApplication.Status.SUBMITTED, "Baneshwor", "Kathmandu", "10", "27.687100", "85.342100", locations["baneshwor"]),
            ("p1_far", "demo-applicant-p1-far", "+9779810000202", "Student", LPGApplication.Category.STUDENT, LPGApplication.Status.UNDER_REVIEW, "New Baneshwor", "Kathmandu", "10", "27.700000", "85.350000", None),
            ("p2_near", "demo-applicant-p2-near", "+9779810000203", "Household", LPGApplication.Category.HOUSEHOLD, LPGApplication.Status.SUBMITTED, "Baneshwor", "Kathmandu", "10", "27.687000", "85.342200", None),
            ("allocated", "demo-applicant-allocated", "+9779810000204", "Allocated", LPGApplication.Category.HOUSEHOLD, LPGApplication.Status.ALLOCATED, "Baneshwor", "Kathmandu", "10", "27.688000", "85.343000", None),
            ("sold", "demo-applicant-sold", "+9779810000205", "Sold", LPGApplication.Category.HOUSEHOLD, LPGApplication.Status.ALLOCATED, "Baneshwor", "Kathmandu", "10", "27.689000", "85.344000", None),
            ("delivered", "demo-applicant-delivered", "+9779810000206", "Delivered", LPGApplication.Category.STUDENT, LPGApplication.Status.DELIVERED, "Baneshwor", "Kathmandu", "10", "27.690000", "85.345000", None),
            ("escalated", "demo-applicant-escalated", "+9779810000207", "Escalated", LPGApplication.Category.HOUSEHOLD, LPGApplication.Status.ALLOCATED, "Baneshwor", "Kathmandu", "10", "27.691000", "85.346000", None),
            ("cancelled", "demo-applicant-cancelled", "+9779810000208", "Cancelled", LPGApplication.Category.HOUSEHOLD, LPGApplication.Status.CANCELLED, "Pulchowk", "Lalitpur", "3", "27.680000", "85.316700", locations["pulchowk"]),
            ("rejected", "demo-applicant-rejected", "+9779810000209", "Rejected", LPGApplication.Category.HOUSEHOLD, LPGApplication.Status.REJECTED, "Suryabinayak", "Bhaktapur", "5", "27.671000", "85.429800", None),
        ]
        applicants = {}
        for key, username, mobile, label, category, status, tole, municipality, ward, latitude, longitude, location_unit in specs:
            user = self._ensure_user(username, f"{username}@example.com", "Demo", label, password, applicant_group)
            household, _ = Household.objects.update_or_create(
                created_by=user,
                defaults={
                    "municipality": municipality,
                    "ward": ward,
                    "tole": tole,
                    "house_number": f"D-{key}",
                    "flat_unit": "101" if key in {"p1_near", "delivered"} else "",
                    "family_size": 3,
                    "latitude": Decimal(latitude),
                    "longitude": Decimal(longitude),
                    "location_unit": location_unit,
                    "location_match_confidence": Household.LocationMatchConfidence.CANONICAL if location_unit else Household.LocationMatchConfidence.USER_ENTERED,
                    "members": "Demo member 1\nDemo member 2",
                },
            )
            ApplicantProfile.objects.update_or_create(
                user=user,
                defaults={
                    "mobile_number": mobile,
                    "mobile_verified": key in {"p1_near", "allocated", "delivered"},
                    "household": household,
                },
            )
            application, _ = LPGApplication.objects.update_or_create(
                household=household,
                entitlement_month=LPGApplication._meta.get_field("entitlement_month").default(),
                defaults={
                    "applicant": user,
                    "category": category,
                    "brand_preference": LPGApplication.BrandPreference.ANY,
                    "preferred_brand": brands["nepal_gas"] if key in {"p1_near", "allocated", "delivered"} else None,
                    "status": status,
                },
            )
            application.status = status
            application.save(update_fields=["status", "updated_at"])
            applicants[key] = application
        return applicants

    @staticmethod
    def _seed_inventory(dealer, brand):
        states = [
            ("stock-1", CylinderFill.Status.IN_STOCK, CylinderUnit.Status.ACTIVE),
            ("stock-2", CylinderFill.Status.IN_STOCK, CylinderUnit.Status.ACTIVE),
            ("stock-3", CylinderFill.Status.IN_STOCK, CylinderUnit.Status.ACTIVE),
            ("allocated", CylinderFill.Status.RESERVED, CylinderUnit.Status.ACTIVE),
            ("sold", CylinderFill.Status.SOLD_PENDING_RECEIPT, CylinderUnit.Status.ACTIVE),
            ("escalated", CylinderFill.Status.SOLD_PENDING_RECEIPT, CylinderUnit.Status.ACTIVE),
            ("received", CylinderFill.Status.RECEIPT_CONFIRMED, CylinderUnit.Status.ACTIVE),
            ("returned", CylinderFill.Status.RETURNED_EMPTY, CylinderUnit.Status.ACTIVE),
            ("damaged", CylinderFill.Status.DAMAGED, CylinderUnit.Status.DAMAGED),
        ]
        fills = {}
        for key, fill_status, unit_status in states:
            unit, _ = CylinderUnit.objects.update_or_create(
                manufacturer_serial_number=f"DEMO-SERIAL-{key.upper()}",
                defaults={
                    "dealer": dealer,
                    "brand": brand,
                    "asset_code": f"DEMO-CYL-{key.upper()}",
                    "capacity_kg": Decimal("14.20"),
                    "status": unit_status,
                },
            )
            fill, _ = CylinderFill.objects.update_or_create(
                fill_reference=f"DEMO-FILL-{key.upper()}",
                defaults={
                    "cylinder_unit": unit,
                    "dealer": dealer,
                    "brand": brand,
                    "source_reference": "DEMO-DISPATCH-001",
                    "received_by": dealer.user,
                    "filled_at": timezone.now() - timedelta(days=1),
                    "status": fill_status,
                },
            )
            fills[key] = fill
        return fills

    @staticmethod
    def _seed_allocations(dealer, brand, applicants, fills):
        now = timezone.now()
        completed, _ = AllocationRun.objects.update_or_create(
            dealer=dealer,
            brand=brand,
            requested_quantity=4,
            created_by=dealer.user,
            defaults={
                "status": AllocationRun.Status.COMPLETED,
                "candidate_count": 7,
                "stock_count": 4,
                "selected_count": 4,
                "started_at": now - timedelta(hours=3),
                "completed_at": now - timedelta(hours=2),
                "error_message": "",
            },
        )
        allocation_specs = [
            ("allocated", "allocated", Allocation.Status.RESERVED, 1, "tole", 1.0),
            ("sold", "sold", Allocation.Status.SALE_RECORDED, 2, "tole", 1.0),
            ("delivered", "received", Allocation.Status.RECEIPT_CONFIRMED, 3, "tole", 1.0),
            ("escalated", "escalated", Allocation.Status.ESCALATED, 4, "ward", 0.85),
        ]
        for applicant_key, fill_key, status, rank, location_level, location_score in allocation_specs:
            Allocation.objects.update_or_create(
                application=applicants[applicant_key],
                defaults={
                    "run": completed,
                    "dealer": dealer,
                    "brand": brand,
                    "cylinder_fill": fills[fill_key],
                    "rank": rank,
                    "priority_snapshot": applicants[applicant_key].priority,
                    "location_match_level": location_level,
                    "location_match_score": Decimal(str(location_score)),
                    "distance_meters": Decimal(str(150 + (rank * 275))),
                    "status": status,
                },
            )
        run_specs = [
            (2, AllocationRun.Status.QUEUED, 0, 3, 0, None, None, ""),
            (3, AllocationRun.Status.RUNNING, 6, 3, 0, now - timedelta(minutes=10), None, ""),
            (99, AllocationRun.Status.FAILED, 6, 3, 0, now - timedelta(hours=1), None, "Demo failure: insufficient cylinders for requested quantity."),
        ]
        for quantity, status, candidates, stock, selected, started_at, completed_at, error_message in run_specs:
            AllocationRun.objects.update_or_create(
                dealer=dealer,
                brand=brand,
                requested_quantity=quantity,
                created_by=dealer.user,
                defaults={
                    "status": status,
                    "candidate_count": candidates,
                    "stock_count": stock,
                    "selected_count": selected,
                    "started_at": started_at,
                    "completed_at": completed_at,
                    "error_message": error_message,
                },
            )

    @staticmethod
    def _seed_complaints(applicants):
        Complaint.objects.update_or_create(
            applicant=applicants["delivered"].applicant,
            confirmation_number="DEMO-RECEIPT-001",
            defaults={
                "complaint": "Demo complaint: delivery confirmation arrived late.",
            },
        )
