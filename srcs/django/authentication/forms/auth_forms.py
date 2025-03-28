from django.contrib.auth.forms import UserCreationForm
from authentication.models import CustomUser
from django import forms

# Forms are used to validate user input and to save data to the database using the models.
# This form is used to register a new user, it extends the UserCreationForm class from Django.

# It adds an email field and a privacy_policy field to the form fields.
# The save method is overridden to set the user as inactive, 
# (user will be activated after verifying the email)

class RegistrationForm(UserCreationForm):
    """User registration form"""

    email = forms.EmailField(required=True)
    privacy_policy = forms.BooleanField(required=True)

    class Meta:
        model = CustomUser
        fields = ("username", "email")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.is_active = False
        if commit:
            user.save()
        return user
