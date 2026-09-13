from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.validators import RegexValidator

from brands.models import LPGBrand
from companies.roles import APPLICANT_GROUP
from locations.models import LocationUnit

from .models import ApplicantProfile, Complaint, Household, LPGApplication

User = get_user_model()


def normalize_mobile(value):
    return "".join(value.split()).replace("-", "")


class ApplicantRegistrationForm(forms.Form):
    full_name = forms.CharField(max_length=150, label="Full name")
    mobile_number = forms.CharField(
        max_length=20,
        label="Mobile number",
        validators=[
            RegexValidator(
                r"^\+?[0-9]{7,15}$",
                "Enter a valid mobile number using 7–15 digits.",
            )
        ],
        help_text="This will be your username. OTP verification will be added next.",
    )
    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput,
    )
    password2 = forms.CharField(
        label="Confirm password",
        strip=False,
        widget=forms.PasswordInput,
    )

    def clean_mobile_number(self):
        mobile = normalize_mobile(self.cleaned_data["mobile_number"])
        if User.objects.filter(username=mobile).exists() or ApplicantProfile.objects.filter(
            mobile_number=mobile
        ).exists():
            raise forms.ValidationError("An account with this mobile number already exists.")
        return mobile

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "The passwords do not match.")
        if password1:
            try:
                validate_password(password1)
            except forms.ValidationError as error:
                self.add_error("password1", error)
        return cleaned

    def save(self):
        user = User.objects.create_user(
            username=self.cleaned_data["mobile_number"],
            password=self.cleaned_data["password1"],
        )
        first_name, _, last_name = self.cleaned_data["full_name"].partition(" ")
        user.first_name = first_name
        user.last_name = last_name
        user.save(update_fields=["first_name", "last_name"])
        user.groups.add(Group.objects.get(name=APPLICANT_GROUP))
        ApplicantProfile.objects.create(
            user=user,
            mobile_number=self.cleaned_data["mobile_number"],
        )
        return user


class HouseholdForm(forms.ModelForm):
    class Meta:
        model = Household
        fields = [
            "municipality",
            "ward",
            "tole",
            "house_number",
            "flat_unit",
            "family_size",
            "members",
            "location_unit",
        ]
        widgets = {
            "members": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["location_unit"].required = False
        self.fields["location_unit"].label = "Canonical location (optional)"
        self.fields["location_unit"].queryset = LocationUnit.objects.filter(
            is_active=True,
            is_kathmandu_valley=True,
        ).order_by("level", "name_en")


class LPGApplicationForm(forms.ModelForm):
    preferred_brand = forms.ModelChoiceField(
        queryset=LPGBrand.objects.none(),
        required=False,
        label="Preferred LPG brand",
        empty_label="Select a brand",
    )

    class Meta:
        model = LPGApplication
        fields = ["category", "brand_preference", "preferred_brand"]
        help_texts = {
            "category": "Labourer and Student applications are currently proposed as P1 priority.",
            "brand_preference": "Brand assignment rules are still subject to final approval.",
        }

    def __init__(self, *args, household=None, **kwargs):
        self.household = household
        super().__init__(*args, **kwargs)
        self.fields["preferred_brand"].queryset = LPGBrand.objects.filter(
            is_active=True
        ).order_by("brand_id")

    def clean(self):
        cleaned = super().clean()
        preference = cleaned.get("brand_preference")
        preferred_brand = cleaned.get("preferred_brand")
        if preference == LPGApplication.BrandPreference.SPECIFIC and not preferred_brand:
            self.add_error(
                "preferred_brand",
                "Select the preferred brand or choose Any available brand.",
            )
        if preference == LPGApplication.BrandPreference.ANY:
            cleaned["preferred_brand"] = None
        if self.household:
            existing = LPGApplication.objects.filter(
                household=self.household,
                entitlement_month=LPGApplication._meta.get_field(
                    "entitlement_month"
                ).default(),
            ).exclude(status__in=[LPGApplication.Status.CANCELLED, LPGApplication.Status.REJECTED])
            if existing.exists():
                raise forms.ValidationError(
                    "This household already has an application for the current month."
                )
        return cleaned


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ["confirmation_number", "complaint"]
        labels = {
            "confirmation_number": "Confirmation number (optional)",
            "complaint": "Complaint",
        }
        widgets = {
            "complaint": forms.Textarea(attrs={"rows": 5}),
        }
