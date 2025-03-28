from django.contrib.auth.models import AbstractUser
from cryptography.fernet import Fernet
from django.utils import timezone
from django.conf import settings
from django.db import models
from django.apps import apps
import logging
import hashlib

# This model is used to store the user information and manage the user's account

logger = logging.getLogger(__name__)

class CustomUser(AbstractUser):
    id = models.AutoField(primary_key=True) # id is the primary key for the user
    DEFAULT_PROFILE_IMAGE = (
        "https://ui-avatars.com/api/?name={}&background=random&length=2"
    )

    def profile_image_path(instance, filename):
        """Returns the path for the profile image"""
        ext = filename.split(".")[-1]
        return f"profile_images/{instance.username}.{ext}"

    fortytwo_image = models.URLField(max_length=500, blank=True, null=True)
    profile_image = models.ImageField(
        upload_to=profile_image_path, null=True, blank=True
    )
    fortytwo_id = models.CharField(max_length=50, blank=True, null=True)
    is_fortytwo_user = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=255, blank=True, null=True)
    email_token_created_at = models.DateTimeField(null=True, blank=True)
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=100, blank=True, null=True)
    last_2fa_code = models.CharField(max_length=6, blank=True, null=True)
    last_2fa_time = models.DateTimeField(null=True, blank=True)
    pending_email = models.EmailField(blank=True, null=True)
    pending_email_token = models.CharField(max_length=255, blank=True, null=True)
    inactivity_notified = models.BooleanField(default=False)
    inactivity_notification_date = models.DateTimeField(null=True, blank=True)
    email_hash = models.CharField(max_length=64, db_index=True, unique=True, null=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def get_profile_image_url(self):
        """Get the URL for the profile image of 42 API"""
        if self.profile_image and hasattr(self.profile_image, "url"):
            return self.profile_image.url
        if self.is_fortytwo_user and self.fortytwo_image:
            return self.fortytwo_image
        return self.DEFAULT_PROFILE_IMAGE.format(self.username[:2].upper())

    @property
    def fortytwo_image_url(self):
        """Returns the URL for the profile image from 42 API"""
        return (
            self.fortytwo_image
            if self.is_fortytwo_user
            else self.get_profile_image_url()
        )

    @property
    def decrypted_email(self):
        """Returns the decrypted email for use in the application"""
        try:
            if not hasattr(settings, 'ENCRYPTION_KEY') or not settings.ENCRYPTION_KEY:
                logger.error("ENCRYPTION_KEY not found in settings or is empty")
                return self.email
                
            if self.email:
                if self.email.startswith('gAAAAAB'):  # If it's encrypted (Fernet prefix - gAAAAAB)
                    cipher_suite = Fernet(settings.ENCRYPTION_KEY)
                    return cipher_suite.decrypt(self.email.encode()).decode()
                return self.email  # If it's not encrypted
        except Exception as e:
            logger.error(f"Error decrypting email for user {self.id}: {str(e)}")
            return self.email
        return None

    def _generate_email_hash(self, email):
        """Generate a hash for email comparison
		   This is used to compare emails without storing them in plain text.
           to know if a mail user is already registered.
           
           Fernet encryption is used to store the email in the database.
           It encripted with a different key each time and it cant be used to compare emails.
		"""
        if not email:
            return None
        normalized_email = email.lower().strip() # Normalize (lowercase and strip)
        return hashlib.sha256(normalized_email.encode()).hexdigest() # Hash email for comparison with other users

    def save(self, *args, **kwargs):
        """Encrypt email before saving"""
        if self.email and not self.email.startswith('gAAAAAB'):
            try:
                if not hasattr(settings, 'ENCRYPTION_KEY') or not settings.ENCRYPTION_KEY:
                    logger.error("ENCRYPTION_KEY not found in settings or is empty")
                    super().save(*args, **kwargs)
                    return
                    
                # Generate hash before encryption
                self.email_hash = self._generate_email_hash(self.email)
                    
                cipher_suite = Fernet(settings.ENCRYPTION_KEY)
                self.email = cipher_suite.encrypt(self.email.encode()).decode()
            except Exception as e:
                logger.error(f"Error encrypting email for user {self.id}: {str(e)}")
        super().save(*args, **kwargs)

    def get_last_activity(self):
        """
        Returns the most recent activity time from last_login, sessions or date_joined.
        
        This method determines the user's most recent activity by comparing:
        - Last login timestamp
        - Session activity records
        - Account creation date (as fallback)
        
        This is used by cleanup tasks to determine if a user should be notified or deleted.
        """
        UserSession = apps.get_model('authentication', 'UserSession')
        
        # If user has never logged in, use date_joined
        last_activity = self.last_login or self.date_joined
        
        # Consider active sessions
        active_session = UserSession.objects.filter(
            user=self
        ).order_by('-last_activity').first()
        
        if active_session and active_session.last_activity > last_activity:
            return active_session.last_activity
        
        return last_activity

    def should_notify_inactivity(self):
        """ Check if user should receive inactivity warning."""
        if self.inactivity_notified or not self.last_login:
            return False
            
        last_activity = self.get_last_activity()
        inactive_seconds = (timezone.now() - last_activity).total_seconds()
        return inactive_seconds >= settings.INACTIVITY_WARNING

    def is_inactive_for_too_long(self):
        """ Check if user should be deleted due to inactivity."""
        if not self.inactivity_notified or not self.inactivity_notification_date:
            return False

        current_time = timezone.now()
        warning_age = (current_time - self.inactivity_notification_date).total_seconds()
        total_inactive = (current_time - self.get_last_activity()).total_seconds()

        return (warning_age >= settings.INACTIVITY_WARNING and 
                total_inactive >= settings.INACTIVITY_THRESHOLD)

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return self.username


class PreviousPassword(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="previous_passwords"
    )
    password = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "-created_at"])]
        verbose_name = "Contraseña anterior"
        verbose_name_plural = "Contraseñas anteriores"

    def save(self, *args, **kwargs):
        if self.__class__.objects.filter(user=self.user).count() >= 3:
            oldest = (
                self.__class__.objects.filter(user=self.user)
                .order_by("created_at")
                .first()
            )
            if oldest:
                oldest.delete()
        super().save(*args, **kwargs)
