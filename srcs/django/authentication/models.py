from django.db import models
from django.contrib.auth.models import AbstractUser
import os

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
        initials = self.username[:2].upper()
        return self.DEFAULT_PROFILE_IMAGE.format(initials)

    @property
    def fortytwo_image_url(self):
        if self.is_fortytwo_user:
            return self.fortytwo_image or self.get_profile_image_url()
        return self.get_profile_image_url()

    def save(self, *args, **kwargs):
        if not self.profile_image and not self.is_fortytwo_user:
            # No establecer la URL directamente en profile_image
            pass
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return self.username