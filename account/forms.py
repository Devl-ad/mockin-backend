from django import forms
from django.contrib.auth import get_user_model

from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm

from django.contrib.auth.forms import SetPasswordForm

User = get_user_model()


class SetPasswordForm(SetPasswordForm):
    class Meta:
        model = get_user_model()
        fields = ["new_password1", "new_password2"]


class RegisterForm(UserCreationForm):
    """
    The default

    """

    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
                "placeholder": "First Name",
                "autocomplete": False,
            }
        ),
        label="First Name",
        required=True,
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
                "placeholder": "Last Name",
                "autocomplete": False,
            }
        ),
        label="Last Name",
        required=True,
    )
    email = forms.EmailField(
        max_length=80,
        widget=forms.TextInput(
            attrs={
                "type": "email",
                "class": "form-control",
                "placeholder": "Email",
                "autocomplete": False,
            }
        ),
        label="Email",
        required=True,
    )

    password1 = forms.CharField(
        max_length=10,
        min_length=6,
        label=" ",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Password",
                "class": "form-control",
                "autocomplete": False,
            }
        ),
    )
    password2 = forms.CharField(
        max_length=10,
        min_length=6,
        label="",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Confirm Password",
                "class": "form-control",
                "autocomplete": False,
            }
        ),
    )

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "password1", "password2"]


class LoginForm(forms.ModelForm):
    email = forms.EmailField(
        max_length=80,
        widget=forms.TextInput(
            attrs={"type": "email", "class": "form-control", "placeholder": "Email"}
        ),
        label="Email",
        required=True,
    )
    password = forms.CharField(
        max_length=10,
        min_length=6,
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Password",
                "class": "form-control",
            }
        ),
    )

    class Meta:
        model = User
        fields = ("email", "password")

    def clean(self):
        if self.is_valid():
            if not authenticate(
                email=self.cleaned_data["email"], password=self.cleaned_data["password"]
            ):
                raise forms.ValidationError("Invalid Email and Password")
