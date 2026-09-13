from types import SimpleNamespace

from django.test import SimpleTestCase

from dealers.models import DealerCoverageArea

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
