from django.core.management import call_command
from django.test import TestCase

from .models import LPGBrand


class BrandCatalogTests(TestCase):
    def test_seed_command_upserts_stable_catalog_ids(self):
        call_command("seed_brands", verbosity=0)

        self.assertEqual(LPGBrand.objects.count(), 55)
        self.assertEqual(LPGBrand.objects.get(brand_id=1).code, "ambar-gas")
        self.assertEqual(LPGBrand.objects.get(brand_id=29).name_en, "Nepal Gas")
        self.assertEqual(LPGBrand.objects.get(brand_id=55).name_ne, "त्रिवेणी ग्यास")

        call_command("seed_brands", verbosity=0)
        self.assertEqual(LPGBrand.objects.count(), 55)
