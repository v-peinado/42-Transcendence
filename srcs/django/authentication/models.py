from authentication.models.user import CustomUser, PreviousPassword
from authentication.models.session import UserSession
from django.contrib.auth.models import AbstractUser

__all__ = ['CustomUser', 'PreviousPassword', 'UserSession']

class CustomUser(AbstractUser):
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    objects = CustomUserManager()
    all_objects = models.Manager()
    
    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save()
        
    @property
    def is_deleted(self):
        return self.deleted_at is not None
