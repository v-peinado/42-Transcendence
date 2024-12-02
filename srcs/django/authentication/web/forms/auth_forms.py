from django import forms
from django.contrib.auth.forms import UserCreationForm
from ...models import CustomUser
from django.core.exceptions import ValidationError
import re
from django.core.validators import RegexValidator

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    privacy_policy = forms.BooleanField(required=True)
    username = forms.CharField(
        validators=[
            RegexValidator(
                regex='^[\w.@+-]+$',
                message='Nombre de usuario contiene caracteres no permitidos'
            )
        ]
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username.startswith('42.'):
            raise ValidationError("El prefijo '42.' está reservado para usuarios de 42")
        
        if not all(char.isprintable() and not char.isspace() for char in username):
            raise ValidationError("El nombre de usuario no puede contener espacios ni caracteres especiales")
        
        return username.lower()

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if re.match(r'.*@student\.42.*\.com$', email.lower()):
            raise ValidationError("Los correos con dominio @student.42*.com están reservados para usuarios de 42")
        
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("Este email ya está en uso")
        
        return email.lower()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.is_active = False  # Usuario inactivo hasta verificar email
        if commit:
            user.save()
        return user

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    remember = forms.BooleanField(required=False)