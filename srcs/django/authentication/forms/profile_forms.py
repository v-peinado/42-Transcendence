from django import forms
from django.core.exceptions import ValidationError
from authentication.models import CustomUser
import re

class ProfileUpdateForm(forms.ModelForm):
    """Formulario para actualizar el perfil del usuario"""
    class Meta:
        model = CustomUser
        fields = ['email', 'profile_image']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user and self.user.is_fortytwo_user:
            self.fields['email'].disabled = True

    def clean_email(self):
        """Validar el email"""
        email = self.cleaned_data.get('email')
        
        # No validar si es usuario de 42
        if self.user and self.user.is_fortytwo_user:
            return self.user.email

        # Validar que no sea un email de 42
        if re.match(r'.*@student\.42.*\.com$', email.lower()):
            raise ValidationError("Los correos con dominio @student.42*.com están reservados para usuarios de 42")

        # Validar que el email no esté en uso por otro usuario
        if CustomUser.objects.exclude(id=self.user.id).filter(email=email).exists():
            raise ValidationError("Este email ya está en uso")

        return email.lower()

    def clean_profile_image(self):
        """Validar la imagen de perfil"""
        image = self.cleaned_data.get('profile_image')
        if image:
            # Validar tamaño (max 5MB)
            if image.size > 5 * 1024 * 1024:
                raise ValidationError("La imagen no debe exceder 5MB")
            
            # Validar extensión
            valid_extensions = ['jpg', 'jpeg', 'png', 'gif']
            ext = image.name.split('.')[-1].lower()
            if ext not in valid_extensions:
                raise ValidationError(f"Formato no permitido. Use: {', '.join(valid_extensions)}")
        
        return image