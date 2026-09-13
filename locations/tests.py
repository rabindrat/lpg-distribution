from types import SimpleNamespace
import json
from tempfile import NamedTemporaryFile

from django.core.management import call_command
from django.test import SimpleTestCase
from django.test import TestCase

from dealers.models import DealerCoverageArea

from .models import LocationUnit
from .services import coverage_match, normalize_location_text


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
