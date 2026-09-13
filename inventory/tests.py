from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from brands.models import LPGBrand
from dealers.models import DealerBrandAuthorization, DealerProfile

from .models import CylinderFill, CylinderUnit
from .services import receive_cylinder_batch


User = get_user_model()


class CylinderInventoryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_brands", verbosity=0)

    def setUp(self):
        self.brand = LPGBrand.objects.get(brand_id=29)
        self.user = User.objects.create_user(username="inventory-dealer", password="password")
        self.dealer = DealerProfile.objects.create(
            user=self.user,
            dealer_name="Inventory Dealer",
            proprietor_name="Test Owner",
            mobile_number="+9779812345699",
            email="inventory@example.com",
            municipality="Kathmandu",
            ward="1",
            tole="Tole",
            address="Address",
            house_plot_number="1",
            authorization_license="LIC-INV",
            gps_latitude=Decimal("27.700000"),
            gps_longitude=Decimal("85.300000"),
            shop_photo="dealers/shop-photos/shop.jpg",
            status=DealerProfile.Status.ACTIVE,
        )
        DealerBrandAuthorization.objects.create(
            dealer=self.dealer,
            brand=self.brand,
            status=DealerBrandAuthorization.Status.ACTIVE,
        )

    def test_receipt_creates_individual_unit_and_fill_cycle_records(self):
        fills = receive_cylinder_batch(
            dealer=self.dealer,
            brand=self.brand,
            quantity=3,
            created_by=self.user,
            source_reference="DISPATCH-42",
        )

        self.assertEqual(len(fills), 3)
        self.assertEqual(CylinderUnit.objects.filter(dealer=self.dealer).count(), 3)
        self.assertEqual(CylinderFill.objects.filter(dealer=self.dealer).count(), 3)
        self.assertEqual(
            CylinderFill.objects.filter(source_reference="DISPATCH-42").count(), 3
        )
        self.assertEqual(
            CylinderFill.objects.filter(status=CylinderFill.Status.IN_STOCK).count(), 3
        )
        self.assertEqual(len({fill.fill_reference for fill in fills}), 3)
