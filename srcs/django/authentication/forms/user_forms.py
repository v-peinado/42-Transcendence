from ..services.password_service import PasswordService
from django.core.exceptions import ValidationError
from django.utils.html import escape
from ..models import CustomUser
from django import forms

# Forms are used to validate user input and to display forms in the frontend using Django templates.
# They are used in the views to handle user input and to interact with the database
# This file contains forms related to the user model.
# Each form represent a different action that can be performed by the user and a "column in the database".


class UserForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput(), label="Contraseña")
    password2 = forms.CharField(
        widget=forms.PasswordInput(), label="Confirmar contraseña"
    )

    class Meta:
        model = CustomUser
        fields = ["username", "email"]
        readonly_fields = ["profile_image", "is_fortytwo_user", "fortytwo_id"]

    def clean(self):
        cleaned_data = super().clean()
        username = escape(cleaned_data.get("username", "")).lower()
        email = escape(cleaned_data.get("email", "")).lower()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        try:
            PasswordService.validate_manual_registration(
                username=username, email=email, password1=password1, password2=password2
            )
        except ValidationError as e:
            raise forms.ValidationError(str(e))

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["username"]
        user.email = self.cleaned_data["email"]

        if commit:
            password = self.cleaned_data["password1"]
            user.set_password(password)
            user.save()

        return user


# Login form
class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput())
    remember = forms.BooleanField(required=False)


# Email change form
class EmailChangeForm(forms.Form):
    new_email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())


# Password change form
class PasswordChangeForm(forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput())
    new_password1 = forms.CharField(widget=forms.PasswordInput())
    new_password2 = forms.CharField(widget=forms.PasswordInput())


# Two factor auth form
class TwoFactorVerificationForm(forms.Form):
    code = forms.CharField(max_length=6)


# Password reset form
class PasswordResetForm(forms.Form):
    email = forms.EmailField()
