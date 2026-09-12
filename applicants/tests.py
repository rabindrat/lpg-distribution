from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import ApplicantProfile, Household, LPGApplication

User = get_user_model()


class ApplicantFlowTests(TestCase):
    def test_registration_creates_account_and_redirects_to_household(self):
        self.client.logout()
        response = self.client.post(
            reverse("register"),
            {
                "full_name": "Sita Thapa",
                "mobile_number": "+9779812345679",
                "password1": "A-secure-password-123!",
                "password2": "A-secure-password-123!",
            },
        )
        self.assertRedirects(response, reverse("household"))
        user = User.objects.get(username="+9779812345679")
        self.assertEqual(user.get_full_name(), "Sita Thapa")
        self.assertTrue(ApplicantProfile.objects.filter(user=user).exists())

    def setUp(self):
        self.user = User.objects.create_user(username="+9779812345678", password="password")
        self.profile = ApplicantProfile.objects.create(
            user=self.user,
            mobile_number="+9779812345678",
        )
        self.client.login(username="+9779812345678", password="password")

    def test_household_form_saves_profile_link(self):
        response = self.client.post(
            reverse("household"),
            {
                "municipality": "Kathmandu Metropolitan City",
                "ward": "10",
                "tole": "Baneshwor",
                "house_number": "125",
                "flat_unit": "A",
                "family_size": "4",
                "members": "Sita Thapa\nRam Thapa",
            },
        )
        self.assertRedirects(response, reverse("apply"))
        self.profile.refresh_from_db()
        self.assertIsNotNone(self.profile.household)
        self.assertEqual(self.profile.household.flat_unit, "A")

    def test_application_is_created_with_priority_and_due_date(self):
        household = Household.objects.create(
            municipality="Kathmandu Metropolitan City",
            ward="10",
            tole="Baneshwor",
            house_number="125",
            family_size=4,
            created_by=self.user,
        )
        self.profile.household = household
        self.profile.save(update_fields=["household"])
        response = self.client.post(
            reverse("apply"),
            {
                "category": LPGApplication.Category.STUDENT,
                "brand_preference": LPGApplication.BrandPreference.ANY,
                "preferred_brand_name": "",
            },
        )
        self.assertRedirects(response, reverse("dashboard"))
        application = LPGApplication.objects.get(household=household)
        self.assertEqual(application.priority, "P1")
        self.assertEqual(application.due_date, timezone.localdate() + timedelta(days=2))
        self.assertTrue(application.reference.startswith("APP-"))

    def test_second_application_for_same_household_and_month_is_rejected(self):
        household = Household.objects.create(
            municipality="Kathmandu Metropolitan City",
            ward="10",
            tole="Baneshwor",
            house_number="125",
            family_size=4,
            created_by=self.user,
        )
        self.profile.household = household
        self.profile.save(update_fields=["household"])
        LPGApplication.objects.create(
            applicant=self.user,
            household=household,
            category=LPGApplication.Category.HOUSEHOLD,
        )
        response = self.client.post(
            reverse("apply"),
            {
                "category": LPGApplication.Category.HOUSEHOLD,
                "brand_preference": LPGApplication.BrandPreference.ANY,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already has an application")
        self.assertEqual(LPGApplication.objects.filter(household=household).count(), 1)
