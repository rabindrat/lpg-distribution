from types import SimpleNamespace
import json
from tempfile import NamedTemporaryFile

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import SimpleTestCase
from django.test import TestCase

from allocations.models import Allocation, AllocationRun
from applicants.models import Complaint, LPGApplication
from dealers.models import DealerProfile
from inventory.models import CylinderFill
from dealers.models import DealerCoverageArea

from .models import LocationUnit
from .services import coverage_match, normalize_location_text


User = get_user_model()


class LocationMatchingTests(SimpleTestCase):
    def test_normalization_handles_case_and_punctuation(self):
        self.assertEqual(
            normalize_location_text("  New-Baneshwor,  "),
            "new baneshwor",
        )

    def test_normalization_preserves_unicode_words(self):
        self.assertEqual(normalize_location_text("बानेश्वर"), "बानेश्वर")

    def test_tole_coverage_accepts_a_conservative_fuzzy_match(self):
        household = SimpleNamespace(
            municipality="Kathmandu",
            ward="10",
            tole="New Baneshwor",
            location_unit_id=None,
        )
        coverage = SimpleNamespace(
            is_active=True,
            coverage_level=DealerCoverageArea.CoverageLevel.TOLE,
            municipality="Kathmandu",
            ward="10",
            tole="New-Baneshwar",
            location_unit_id=None,
            CoverageLevel=DealerCoverageArea.CoverageLevel,
        )

        score, level = coverage_match(household, coverage)

        self.assertGreaterEqual(score, 0.88)
        self.assertEqual(level, DealerCoverageArea.CoverageLevel.TOLE)

    def test_ward_coverage_accepts_missing_tole(self):
        household = SimpleNamespace(
            municipality="Kathmandu",
            ward="10",
            tole="",
            location_unit_id=None,
        )
        coverage = SimpleNamespace(
            is_active=True,
            coverage_level=DealerCoverageArea.CoverageLevel.WARD,
            municipality="Kathmandu",
            ward="10",
            tole="",
            location_unit_id=None,
            CoverageLevel=DealerCoverageArea.CoverageLevel,
        )

        score, level = coverage_match(household, coverage)

        self.assertEqual(score, 0.85)
        self.assertEqual(level, DealerCoverageArea.CoverageLevel.WARD)


class LocationCatalogImportTests(TestCase):
    def test_catalog_import_upserts_parents_and_aliases(self):
        payload = {
            "locations": [
                {
                    "code": "NP-KTM-KMC",
                    "level": "municipality",
                    "name_en": "Kathmandu Metropolitan City",
                    "district_name": "Kathmandu",
                    "is_kathmandu_valley": True,
                },
                {
                    "code": "NP-KTM-KMC-W10",
                    "level": "ward",
                    "name_en": "Ward 10",
                    "parent_code": "NP-KTM-KMC",
                    "district_name": "Kathmandu",
                    "is_kathmandu_valley": True,
                },
                {
                    "code": "NP-KTM-KMC-W10-BANESHWOR",
                    "level": "tole",
                    "name_en": "Baneshwor",
                    "aliases": ["New Baneshwor"],
                    "parent_code": "NP-KTM-KMC-W10",
                    "district_name": "Kathmandu",
                    "is_kathmandu_valley": True,
                },
            ]
        }
        with NamedTemporaryFile(mode="w", suffix=".json") as catalog:
            json.dump(payload, catalog)
            catalog.flush()
            call_command("import_location_catalog", catalog.name, source="approved-test")

        tole = LocationUnit.objects.get(code="NP-KTM-KMC-W10-BANESHWOR")
        self.assertEqual(tole.parent.code, "NP-KTM-KMC-W10")
        self.assertEqual(tole.alias_records.get().source, "approved-test")


class DemoSeedCommandTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_brands", verbosity=0)
        call_command("seed_companies", verbosity=0)
        call_command("seed_dealers", verbosity=0)

    def test_demo_seed_is_idempotent_and_covers_workflow_states(self):
        call_command("seed_demo_data", password="test-password", verbosity=0)
        call_command("seed_demo_data", password="test-password", verbosity=0)

        self.assertEqual(User.objects.filter(username__startswith="demo-").count(), 14)
        self.assertEqual(DealerProfile.objects.filter(user__username__startswith="demo-dealer-").count(), 4)
        self.assertEqual(LPGApplication.objects.filter(applicant__username__startswith="demo-applicant-").count(), 9)
        self.assertEqual(CylinderFill.objects.filter(fill_reference__startswith="DEMO-").count(), 9)
        self.assertEqual(Allocation.objects.filter(application__applicant__username__startswith="demo-applicant-").count(), 4)
        self.assertEqual(AllocationRun.objects.filter(created_by__username="demo-dealer-active").count(), 4)
        self.assertEqual(Complaint.objects.filter(applicant__username="demo-applicant-delivered").count(), 1)
