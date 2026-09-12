from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import DealerBrandAuthorization, DealerProfile, DealerRegistry

User = get_user_model()


class DealerFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_brands", verbosity=0)
        call_command("seed_dealers", verbosity=0)

    def registration_data(self):
        return {
            "dealer_name": "Baneshwor LPG Centre",
            "proprietor_name": "Ram Thapa",
            "mobile_number": "+9779812345688",
            "email": "ram@example.com",
            "municipality": "Kathmandu Metropolitan City",
            "ward": "10",
            "tole": "Baneshwor",
            "address": "Main road, Baneshwor",
            "house_plot_number": "125A",
            "brand": "29",
            "authorization_license": "LIC-12345",
            "gps_latitude": "27.6869",
            "gps_longitude": "85.3420",
            "password1": "A-secure-password-123!",
            "password2": "A-secure-password-123!",
        }

    def test_dealer_registration_creates_submitted_profile(self):
        data = self.registration_data()
        data["shop_photo"] = SimpleUploadedFile("shop.jpg", b"photo", content_type="image/jpeg")
        response = self.client.post(reverse("dealer-register"), data)
        self.assertRedirects(response, reverse("dealer-dashboard"))
        dealer = DealerProfile.objects.get(mobile_number="+9779812345688")
        self.assertEqual(dealer.status, DealerProfile.Status.SUBMITTED)
        self.assertEqual(dealer.display_brand, "Nepal Gas")
        self.assertTrue(
            DealerBrandAuthorization.objects.filter(
                dealer=dealer, brand_id=29, is_primary=True
            ).exists()
        )

    def test_dealer_dashboard_requires_dealer_profile(self):
        user = User.objects.create_user(username="123456789", password="password")
        self.client.force_login(user)
        response = self.client.get(reverse("dealer-dashboard"))
        self.assertRedirects(
            response,
            reverse("dealer-register"),
            fetch_redirect_response=False,
        )

    def test_admin_approval_moves_verified_dealer_to_active(self):
        user = User.objects.create_user(username="dealer-user", password="password")
        dealer = DealerProfile.objects.create(
            user=user,
            dealer_name="Test Dealer",
            proprietor_name="Test Owner",
            mobile_number="1234567890",
            email="dealer@example.com",
            municipality="Kathmandu",
            ward="1",
            tole="Tole",
            address="Address",
            house_plot_number="1",
            authorization_license="LIC-1",
            gps_latitude="27.700000",
            gps_longitude="85.300000",
            shop_photo="dealers/shop-photos/shop.jpg",
            status=DealerProfile.Status.PENDING_APPROVAL,
        )
        approver = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="password"
        )
        dealer.approve(approver)
        dealer.refresh_from_db()
        self.assertEqual(dealer.status, DealerProfile.Status.ACTIVE)
        self.assertEqual(dealer.approved_by, approver)

    def test_seeded_dealer_can_be_claimed_during_registration(self):
        data = self.registration_data()
        data.update(
            {
                "registry_dealer": "1",
                "dealer_name": "A M Kirana Store",
                "proprietor_name": "Lal Bahadur Pun",
                "mobile_number": "9803015389",
                "address": "Buddha Marga, Godawari",
                "municipality": "Godawari",
                "ward": "1",
            }
        )
        data["shop_photo"] = SimpleUploadedFile("shop.jpg", b"photo", content_type="image/jpeg")
        response = self.client.post(reverse("dealer-register"), data)
        self.assertRedirects(response, reverse("dealer-dashboard"))
        registry = DealerRegistry.objects.get(registry_id=1)
        self.assertEqual(registry.status, DealerRegistry.Status.CLAIMED)
        self.assertEqual(registry.onboarded_dealer.dealer_name, "A M Kirana Store")
        self.assertEqual(registry.phones, ["9803015389"])

    def test_unique_seeded_phone_auto_reconciles_without_selection(self):
        data = self.registration_data()
        data.update(
            {
                "dealer_name": "Seeded Dealer Name",
                "mobile_number": "9803015389",
            }
        )
        data["shop_photo"] = SimpleUploadedFile("shop.jpg", b"photo", content_type="image/jpeg")
        response = self.client.post(reverse("dealer-register"), data)
        self.assertRedirects(response, reverse("dealer-dashboard"))
        self.assertEqual(
            DealerRegistry.objects.get(registry_id=1).status,
            DealerRegistry.Status.CLAIMED,
        )
