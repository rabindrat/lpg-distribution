from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from applicants.models import ApplicantProfile, Household, LPGApplication
from brands.models import LPGBrand
from dealers.models import DealerBrandAuthorization, DealerCoverageArea, DealerProfile
from inventory.models import CylinderFill
from inventory.services import receive_cylinder_batch
from locations.models import LocationAlias, LocationUnit

from .models import Allocation, AllocationRun
from .services import execute_allocation_run, queue_allocation_run
from .tasks import run_allocation


User = get_user_model()


class AllocationTaskTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_brands", verbosity=0)

    def setUp(self):
        self.brand = LPGBrand.objects.get(brand_id=29)
        self.user = User.objects.create_user(username="dealer-user", password="password")
        self.dealer = DealerProfile.objects.create(
            user=self.user,
            dealer_name="Baneshwor LPG Centre",
            proprietor_name="Ram Thapa",
            mobile_number="+9779812345600",
            email="dealer@example.com",
            municipality="Kathmandu",
            ward="10",
            tole="Baneshwor",
            address="Main road",
            house_plot_number="1",
            authorization_license="LIC-1",
            gps_latitude=Decimal("27.686900"),
            gps_longitude=Decimal("85.342000"),
            shop_photo="dealers/shop-photos/shop.jpg",
            status=DealerProfile.Status.ACTIVE,
        )
        DealerBrandAuthorization.objects.create(
            dealer=self.dealer,
            brand=self.brand,
            status=DealerBrandAuthorization.Status.ACTIVE,
            is_primary=True,
        )
        DealerCoverageArea.objects.create(
            dealer=self.dealer,
            coverage_level=DealerCoverageArea.CoverageLevel.WARD,
            municipality="Kathmandu",
            ward="10",
            created_by=self.user,
        )

    def create_application(self, username, category, latitude, longitude, brand=None):
        user = User.objects.create_user(username=username, password="password")
        profile = ApplicantProfile.objects.create(user=user, mobile_number=username)
        household = Household.objects.create(
            municipality="Kathmandu",
            ward="10",
            tole=username,
            house_number="1",
            family_size=3,
            latitude=latitude,
            longitude=longitude,
            created_by=user,
        )
        profile.household = household
        profile.save(update_fields=["household"])
        return LPGApplication.objects.create(
            applicant=user,
            household=household,
            category=category,
            preferred_brand=brand,
        )

    def create_run(self, quantity=10):
        receive_cylinder_batch(
            dealer=self.dealer,
            brand=self.brand,
            quantity=quantity,
            created_by=self.user,
        )
        return AllocationRun.objects.create(
            dealer=self.dealer,
            brand=self.brand,
            requested_quantity=quantity,
            created_by=self.user,
        )

    def test_p1_is_selected_before_closer_p2_and_p1_is_distance_sorted(self):
        p2_close = self.create_application(
            "p2-close", LPGApplication.Category.HOUSEHOLD, "27.687000", "85.342100"
        )
        p1_far = self.create_application(
            "p1-far", LPGApplication.Category.STUDENT, "27.700000", "85.350000"
        )
        p1_near = self.create_application(
            "p1-near", LPGApplication.Category.LABOURER, "27.687000", "85.342100"
        )

        run = self.create_run(quantity=2)
        result = execute_allocation_run(run.pk)

        self.assertEqual(result["selected_count"], 2)
        self.assertEqual(
            list(Allocation.objects.filter(run=run).values_list("application", flat=True)),
            [p1_near.pk, p1_far.pk],
        )
        self.assertEqual(p2_close.status, LPGApplication.Status.SUBMITTED)
        self.assertEqual(
            CylinderFill.objects.filter(
                dealer=self.dealer,
                status=CylinderFill.Status.RESERVED,
            ).count(),
            2,
        )

    def test_specific_brand_application_is_excluded(self):
        other_brand = LPGBrand.objects.get(brand_id=30)
        application = self.create_application(
            "other-brand",
            LPGApplication.Category.HOUSEHOLD,
            "27.687000",
            "85.342100",
            brand=other_brand,
        )

        execute_allocation_run(self.create_run().pk)

        self.assertFalse(Allocation.objects.filter(application=application).exists())

    def test_stewarded_tole_alias_is_used_for_allocation_matching(self):
        municipality = LocationUnit.objects.create(
            code="NP-KTM-KMC",
            level=LocationUnit.Level.MUNICIPALITY,
            name_en="Kathmandu Metropolitan City",
            normalized_name="kathmandu",
            is_kathmandu_valley=True,
        )
        ward = LocationUnit.objects.create(
            code="NP-KTM-KMC-W10",
            level=LocationUnit.Level.WARD,
            name_en="Ward 10",
            normalized_name="ward 10",
            parent=municipality,
            is_kathmandu_valley=True,
        )
        tole = LocationUnit.objects.create(
            code="NP-KTM-KMC-W10-BANESHWOR",
            level=LocationUnit.Level.TOLE,
            name_en="Baneshwor",
            normalized_name="baneshwor",
            parent=ward,
            is_kathmandu_valley=True,
        )
        LocationAlias.objects.create(location=tole, alias="Naya Baneshwor")
        DealerCoverageArea.objects.create(
            dealer=self.dealer,
            coverage_level=DealerCoverageArea.CoverageLevel.TOLE,
            municipality="Kathmandu",
            ward="10",
            tole="Baneshwor",
            location_unit=tole,
            created_by=self.user,
        )
        application = self.create_application(
            "alias-match",
            LPGApplication.Category.HOUSEHOLD,
            "27.687000",
            "85.342100",
        )
        application.household.tole = "Naya Baneshwor"
        application.household.save(update_fields=["tole", "updated_at"])

        allocation_run = self.create_run(quantity=1)
        execute_allocation_run(allocation_run.pk)

        allocation = Allocation.objects.get(application=application)
        self.assertEqual(allocation.location_match_level, DealerCoverageArea.CoverageLevel.TOLE)
        self.assertGreaterEqual(allocation.location_match_score, 0.88)

    def test_task_is_idempotent_after_completion(self):
        application = self.create_application(
            "idempotent", LPGApplication.Category.HOUSEHOLD, None, None
        )
        run = self.create_run(quantity=1)

        first = run_allocation.run(run.pk)
        second = run_allocation.run(run.pk)

        self.assertEqual(first["selected_count"], 1)
        self.assertEqual(second["selected_count"], 1)
        self.assertEqual(Allocation.objects.filter(application=application).count(), 1)
        run.refresh_from_db()
        self.assertEqual(run.status, AllocationRun.Status.COMPLETED)

    def test_queue_publishes_only_after_run_is_persisted(self):
        with patch("allocations.tasks.run_allocation.delay") as delay:
            with self.captureOnCommitCallbacks(execute=True):
                run = queue_allocation_run(
                    dealer=self.dealer,
                    brand=self.brand,
                    requested_quantity=1,
                    created_by=self.user,
                )

        delay.assert_called_once_with(run.pk)
        self.assertEqual(AllocationRun.objects.get(pk=run.pk).status, AllocationRun.Status.QUEUED)

    def test_task_marks_invalid_dealer_run_failed(self):
        self.dealer.status = DealerProfile.Status.SUSPENDED
        self.dealer.save(update_fields=["status", "updated_at"])
        run = self.create_run()

        with self.assertRaises(ValueError):
            run_allocation.run(run.pk)

        run.refresh_from_db()
        self.assertEqual(run.status, AllocationRun.Status.FAILED)
        self.assertIn("active dealer", run.error_message)
