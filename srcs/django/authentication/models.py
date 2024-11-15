from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    DEFAULT_PROFILE_IMAGE = "https://ui-avatars.com/api/?name={}&background=random"
    
    profile_image = models.URLField(max_length=500, blank=True, null=True)
    fortytwo_id = models.CharField(max_length=50, blank=True, null=True)
    is_fortytwo_user = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.profile_image:
            # Genera una imagen por defecto usando las iniciales del usuario
            self.profile_image = self.DEFAULT_PROFILE_IMAGE.format(self.username)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return self.username