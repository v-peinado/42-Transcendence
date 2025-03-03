from django import forms
from django.contrib.auth.forms import UserCreationForm
from authentication.models import CustomUser

class RegistrationForm(UserCreationForm):
    """Formulario de registro de usuario"""
    email = forms.EmailField(required=True)
    privacy_policy = forms.BooleanField(required=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.is_active = False 
        if commit:
            user.save()
        return user