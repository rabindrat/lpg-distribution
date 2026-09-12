from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.validators import RegexValidator

from brands.models import LPGBrand

from .models import DealerProfile

User = get_user_model()


def normalize_mobile(value):
    return "".join(value.split()).replace("-", "")


class DealerRegistrationForm(forms.Form):
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
        super().__init__(*args, **kwargs)
        self.fields["brand"].queryset = LPGBrand.objects.filter(
            is_active=True
        ).order_by("brand_id")

    def clean_mobile_number(self):
        mobile = normalize_mobile(self.cleaned_data["mobile_number"])
        if User.objects.filter(username=mobile).exists() or DealerProfile.objects.filter(
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
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password1"],
        )
        first_name, _, last_name = self.cleaned_data["proprietor_name"].partition(" ")
        user.first_name = first_name
        user.last_name = last_name
        user.save(update_fields=["first_name", "last_name"])
        return DealerProfile.objects.create(
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
            brand=self.cleaned_data["brand"],
            lpg_brand=self.cleaned_data["brand"].name_en,
            authorization_license=self.cleaned_data["authorization_license"],
            gps_latitude=self.cleaned_data["gps_latitude"],
            gps_longitude=self.cleaned_data["gps_longitude"],
            shop_photo=self.cleaned_data["shop_photo"],
            supporting_document=self.cleaned_data.get("supporting_document"),
        )
