from django.db import models
from django.contrib.auth.models import AbstractUser
import os
from django.core.exceptions import ValidationError
import re

class CustomUser(AbstractUser):
    # Modificar la URL para usar las dos primeras letras del username
    DEFAULT_PROFILE_IMAGE = "https://ui-avatars.com/api/?name={}&background=random&length=2"
    
    def profile_image_path(instance, filename):
        ext = filename.split('.')[-1]
        filename = f'{instance.username}.{ext}'
        return f'profile_images/{filename}'
    
    fortytwo_image = models.URLField(max_length=500, blank=True, null=True)  # Nuevo campo
    profile_image = models.ImageField(
        upload_to=profile_image_path,
        null=True,
        blank=True
    )
    fortytwo_id = models.CharField(max_length=50, blank=True, null=True)
    is_fortytwo_user = models.BooleanField(default=False)

    def get_profile_image_url(self):
        if self.profile_image and hasattr(self.profile_image, 'url'):
            return self.profile_image.url
        if self.is_fortytwo_user and self.fortytwo_image:
            return self.fortytwo_image
        initials = self.username[:2].upper()
        return self.DEFAULT_PROFILE_IMAGE.format(initials)

    @property
    def fortytwo_image_url(self):
        if self.is_fortytwo_user:
            return self.fortytwo_image or self.get_profile_image_url()
        return self.get_profile_image_url()

    def save(self, *args, **kwargs):
        self.clean()  # Ejecutar validaciones antes de guardar
        if not self.profile_image and not self.is_fortytwo_user:
            # No establecer la URL directamente en profile_image
            pass
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        
        if self.username and self.username.startswith('42.') and not self.is_fortytwo_user:
            raise ValidationError({
                'username': "El prefijo '42.' está reservado para usuarios de 42"
            })
            
        if self.email and re.match(r'.*@student\.42.*\.com$', self.email.lower()) and not self.is_fortytwo_user:
            raise ValidationError({
                'email': "Los correos con dominio @student.42*.com están reservados para usuarios de 42"
            })

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return self.username