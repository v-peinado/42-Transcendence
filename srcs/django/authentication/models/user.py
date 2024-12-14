from django.db import models
from django.contrib.auth.models import AbstractUser
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
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=255, blank=True, null=True)
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=32, blank=True, null=True)
    last_2fa_code = models.CharField(max_length=6, blank=True, null=True)
    last_2fa_time = models.DateTimeField(null=True)
    pending_email = models.EmailField(blank=True, null=True)
    pending_email_token = models.CharField(max_length=255, blank=True, null=True)

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
            
        if self.username and not all(char.isprintable() and not char.isspace() for char in self.username):
            raise ValidationError({
                'username': "El nombre de usuario no puede contener espacios ni caracteres especiales"
            })

    def anonymize(self):
        """Anonimizar datos del usuario manteniendo integridad referencial"""
        anon_username = f"deleted_user_{self.id}"
        anon_email = f"deleted_{self.id}@anonymous.com"
        
        self.username = anon_username
        self.email = anon_email
        self.first_name = "Deleted"
        self.last_name = "User"
        self.profile_image = None
        self.is_active = False
        self.save()

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return self.username
        
class PreviousPassword(models.Model):
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE,
        related_name='previous_passwords'
    )
    password = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
        verbose_name = 'Contraseña anterior'
        verbose_name_plural = 'Contraseñas anteriores'

    def save(self, *args, **kwargs):
        # Mantener solo las últimas 3 contraseñas
        if self.__class__.objects.filter(user=self.user).count() >= 3:
            oldest_password = self.__class__.objects.filter(
                user=self.user
            ).order_by('created_at').first()
            if oldest_password:
                oldest_password.delete()
        super().save(*args, **kwargs)