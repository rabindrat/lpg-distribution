from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.validators import RegexValidator
import re

from brands.models import LPGBrand
from companies.roles import DEALER_GROUP

from .models import DealerBrandAuthorization, DealerProfile, DealerRegistry

User = get_user_model()


def normalize_mobile(value):
    return "".join(value.split()).replace("-", "")


def normalize_phone(value):
    return re.sub(r"[^0-9]", "", value or "")


class DealerRegistrationForm(forms.Form):
    registry_dealer = forms.ModelChoiceField(
        queryset=DealerRegistry.objects.none(),
        required=False,
        label="Existing dealer/depot record (optional)",
        empty_label="I am a new dealer or my record is not listed",
        help_text="Select your preloaded record to start with the directory details. Phone verification is still required.",
    )
    dealer_name = forms.CharField(max_length=160, label="Dealer / shop name")
    proprietor_name = forms.CharField(max_length=160, label="Proprietor name")
    mobile_number = forms.CharField(
        max_length=20,
        label="Dealer mobile number",
        validators=[
            RegexValidator(
                r"^\+?[0-9]{7,15}$",
                "Enter a valid mobile number using 7–15 digits.",
            )
        ],
    )
    email = forms.EmailField()
    municipality = forms.CharField(max_length=120)
    ward = forms.CharField(max_length=20)
    tole = forms.CharField(max_length=160, label="Tole / street")
    address = forms.CharField(max_length=240, label="Complete address")
    house_plot_number = forms.CharField(max_length=60, label="House / plot number")
    brand = forms.ModelChoiceField(
        queryset=LPGBrand.objects.none(),
        required=False,
        label="LPG brand",
        empty_label="Select a brand",
    )
    authorization_license = forms.CharField(
        max_length=120,
        label="Authorization / license number",
    )
    gps_latitude = forms.DecimalField(
        max_digits=9,
        decimal_places=6,
        min_value=-90,
        max_value=90,
        label="GPS latitude",
    )
    gps_longitude = forms.DecimalField(
        max_digits=9,
        decimal_places=6,
        min_value=-180,
        max_value=180,
        label="GPS longitude",
    )
    shop_photo = forms.FileField(
        label="Fresh shop-front photograph",
        help_text="Required for the company verification workflow.",
    )
    supporting_document = forms.FileField(required=False, label="Supporting document")
    password1 = forms.CharField(label="Password", strip=False, widget=forms.PasswordInput)
    password2 = forms.CharField(
        label="Confirm password",
        strip=False,
        widget=forms.PasswordInput,
    )

    def __init__(self, *args, **kwargs):
        self.registry_matches = []
        super().__init__(*args, **kwargs)
        self.fields["registry_dealer"].queryset = DealerRegistry.objects.filter(
            status=DealerRegistry.Status.UNCLAIMED
        ).select_related("brand")
        self.fields["brand"].queryset = LPGBrand.objects.filter(
            is_active=True
        ).order_by("brand_id")

    def clean_mobile_number(self):
        mobile = normalize_mobile(self.cleaned_data["mobile_number"])
        if User.objects.filter(username=mobile).exists() or DealerProfile.objects.filter(
            mobile_number=mobile
        ).exists():
            raise forms.ValidationError("An account with this mobile number already exists.")
        phone = normalize_phone(mobile)
        self.registry_matches = [
            entry
            for entry in DealerRegistry.objects.filter(
                status=DealerRegistry.Status.UNCLAIMED
            )
            if phone in entry.phones
        ]
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
        registry_dealer = cleaned.get("registry_dealer")
        if registry_dealer and registry_dealer.status != DealerRegistry.Status.UNCLAIMED:
            self.add_error("registry_dealer", "This directory record is no longer available for claiming.")
        if not registry_dealer and len(self.registry_matches) == 1:
            cleaned["registry_dealer"] = self.registry_matches[0]
            registry_dealer = cleaned["registry_dealer"]
        elif not registry_dealer and len(self.registry_matches) > 1:
            self.add_error(
                "mobile_number",
                "This phone number matches multiple directory records. Select the correct dealer record.",
            )
        if registry_dealer and not cleaned.get("brand"):
            cleaned["brand"] = registry_dealer.brand
        if not cleaned.get("brand"):
            self.add_error("brand", "Select an LPG brand.")
        return cleaned

    def save(self):
        user = User.objects.create_user(
            username=self.cleaned_data["mobile_number"],
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password1"],
        )
        first_name, _, last_name = self.cleaned_data["proprietor_name"].partition(" ")
        user.first_name = first_name
        user.last_name = last_name
        user.save(update_fields=["first_name", "last_name"])
        user.groups.add(Group.objects.get(name=DEALER_GROUP))
        dealer = DealerProfile.objects.create(
            user=user,
            dealer_name=self.cleaned_data["dealer_name"],
            proprietor_name=self.cleaned_data["proprietor_name"],
            mobile_number=self.cleaned_data["mobile_number"],
            email=self.cleaned_data["email"],
            municipality=self.cleaned_data["municipality"],
            ward=self.cleaned_data["ward"],
            tole=self.cleaned_data["tole"],
            address=self.cleaned_data["address"],
            house_plot_number=self.cleaned_data["house_plot_number"],
            phones=[normalize_phone(self.cleaned_data["mobile_number"])],
            authorization_license=self.cleaned_data["authorization_license"],
            gps_latitude=self.cleaned_data["gps_latitude"],
            gps_longitude=self.cleaned_data["gps_longitude"],
            shop_photo=self.cleaned_data["shop_photo"],
            supporting_document=self.cleaned_data.get("supporting_document"),
        )
        DealerBrandAuthorization.objects.create(
            dealer=dealer,
            brand=self.cleaned_data["brand"],
            authorization_license=self.cleaned_data["authorization_license"],
            status=DealerBrandAuthorization.Status.PENDING,
            is_primary=True,
        )
        registry_dealer = self.cleaned_data.get("registry_dealer")
        if registry_dealer:
            registry_dealer.dealer_name = dealer.dealer_name
            registry_dealer.contact_person = dealer.proprietor_name
            registry_dealer.phones = list(
                dict.fromkeys(
                    registry_dealer.phones
                    + [normalize_phone(self.cleaned_data["mobile_number"])]
                )
            )
            registry_dealer.address = dealer.address
            registry_dealer.local_level = dealer.municipality
            registry_dealer.ward = dealer.ward
            registry_dealer.onboarded_dealer = dealer
            registry_dealer.status = DealerRegistry.Status.CLAIMED
            registry_dealer.save(
                update_fields=[
                    "dealer_name",
                    "contact_person",
                    "phones",
                    "address",
                    "local_level",
                    "ward",
                    "onboarded_dealer",
                    "status",
                    "updated_at",
                ]
            )
        return dealer
