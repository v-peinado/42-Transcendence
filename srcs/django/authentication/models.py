from authentication.models.user import CustomUser, PreviousPassword
from authentication.models.session import UserSession
from django.contrib.auth.models import AbstractUser

__all__ = ['CustomUser', 'PreviousPassword', 'UserSession']

class CustomUser(AbstractUser):
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    objects = CustomUserManager()
    all_objects = models.Manager()
    
    # Para la autenticación 2FA
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=100, null=True, blank=True)
    last_2fa_code = models.CharField(max_length=6, null=True, blank=True)
    last_2fa_time = models.DateTimeField(null=True, blank=True)
    
    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save()
        
    @property
    def is_deleted(self):
        return self.deleted_at is not None
