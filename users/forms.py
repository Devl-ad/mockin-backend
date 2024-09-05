from django import forms
from .models import Transactions
from account.models import Account, Kyc

from django.contrib.auth.forms import PasswordChangeForm


class ChangePasswordForm(PasswordChangeForm):
    old_password = forms.CharField(
        max_length=10,
        min_length=6,
        label="Current Password",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Enter Current Password",
                "class": "form-control form-control-lg",
                "autocomplete": False,
            }
        ),
    )
    new_password1 = forms.CharField(
        max_length=10,
        min_length=6,
        label="New Password",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Enter New Password",
                "class": "form-control form-control-lg",
                "autocomplete": False,
            }
        ),
    )
    new_password2 = forms.CharField(
        max_length=10,
        min_length=6,
        label="New Password",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Confirm New Password",
                "class": "form-control form-control-lg",
                "autocomplete": False,
            }
        ),
    )

    class Meta:
        model = Account
        field = ["old_password", "new_password1", "new_password2"]


class DepositForm(forms.ModelForm):
    class Meta:
        model = Transactions
        fields = ["amount", "method", "prove_img", "trans_type", "unique_u"]


class KycForm(forms.ModelForm):
    class Meta:
        model = Kyc
        fields = [
            "document_front",
            "document_back",
        ]


class UpdateUserForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = [
            "phone",
            "gender",
            "date_of_birth",
            "country",
            "state",
            "city",
            "address",
            "zipcode",
            "profile_image",
        ]
