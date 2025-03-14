from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import logging
import hashlib
from authentication.models import CustomUser

logger = logging.getLogger(__name__)

class GDPRService:
    @staticmethod
    def export_user_data(user):
        """Exports all user's personal data in dictionary format"""
        return {
            "personal_info": {
                "username": user.username,
                "email": user.decrypted_email,
                "date_joined": user.date_joined,
                "last_login": user.last_login,
                "is_active": user.is_active,
                "is_fortytwo_user": user.is_fortytwo_user,
                "fortytwo_id": user.fortytwo_id if user.is_fortytwo_user else None,
            },
            "profile_data": {
                "profile_image": user.profile_image.url if user.profile_image else None,
                "fortytwo_image": (
                    user.fortytwo_image if user.is_fortytwo_user else None
                ),
            },
            "security_settings": {
                "two_factor_enabled": user.two_factor_enabled,
                "email_verified": user.email_verified,
            },
        }

    @staticmethod
    def anonymize_user(user):
        """Anonymizes user's personal data"""
        try:
            # Generate anonymous data
            anon_username = f"deleted_user_{user.id}"
            anon_email = f"deleted_{user.id}@deleted.local"
            anon_password = "pbkdf2_sha256$deleted_password"
            
            # Update only existing fields
            user.username = anon_username
            user.email = anon_email
            user.password = anon_password
            user.first_name = "Deleted"
            user.last_name = "User"
            user.profile_image = None
            user.fortytwo_image = None
            user.is_active = False
            user.two_factor_enabled = False
            user.two_factor_secret = None
            user.deleted_at = timezone.now()
            user.fortytwo_id = None
            user.pending_email = None
            user.pending_email_token = None
            
            user.email_hash = None
            
            # Save only the fields that exist in the model
            user.save(update_fields=[
                'email', 'username', 'password', 'first_name', 
                'last_name', 'profile_image', 'fortytwo_image', 
                'is_active', 'two_factor_enabled', 'two_factor_secret', 
                'deleted_at', 'fortytwo_id', 'pending_email', 
                'pending_email_token', 'email_hash'
            ])

            return True
        except Exception as e:
            logger.error(f"Error in anonymize_user: {str(e)}")
            raise ValidationError(f"Error anonymizing user: {str(e)}")

    @staticmethod
    def delete_user_data(user):
        """Soft deletes user's account by anonymizing their data"""
        try:
            GDPRService.anonymize_user(user) # anonymize user data
            return True
        except Exception as e:
            raise ValidationError(f"Error deleting user: {str(e)}")

    @classmethod
    def cleanup_inactive_users(cls, email_connection=None):
        """
        Delegates to CleanupService.cleanup_inactive_users
        
        This method is maintained for backward compatibility only.
        All new code should use CleanupService.cleanup_inactive_users() directly.
        """
        from authentication.services.cleanup_service import CleanupService
        logger.info("GDPRService.cleanup_inactive_users called - Delegating to CleanupService")
        return CleanupService.cleanup_inactive_users(email_connection)

    @staticmethod
    def cleanup_unverified_users(max_verification_age=None):
        """
        Delete unverified users that haven't completed email verification.
        
        Args:
            max_verification_age (int): Maximum time in seconds to wait for email verification
        """
        if max_verification_age is None:
            max_verification_age = getattr(settings, 'EMAIL_VERIFICATION_TIMEOUT', 86400)  # Default: 1 day
        
        current_time = timezone.now()
        cutoff_date = current_time - timedelta(seconds=max_verification_age)
        
        # Find unverified users who have exceeded the maximum verification time
        # and who are NOT already anonymized users (starting with "deleted_user_")
        unverified_users = CustomUser.objects.filter(
            email_verified=False,
            is_active=False,
            date_joined__lt=cutoff_date
        ).exclude(
            username__startswith='deleted_user_'
        )
        
        deleted_count = 0
        
        # Process each unverified user
        for user in unverified_users:
            logger.info(
                f"🔥 Deleting unverified user {user.username}:\n"
                f"- Registration date: {user.date_joined}\n"
                f"- Cutoff date: {cutoff_date}\n"
                f"- Current time: {current_time}"
            )
            try:
                # Use delete_user_data for consistency with the rest of the system
                GDPRService.delete_user_data(user)
                deleted_count += 1
            except Exception as e:
                logger.error(f"Error deleting unverified user {user.username}: {str(e)}")
        
        # Only log if there's something to report
        if deleted_count > 0:
            logger.info(f"🧹 Deleted {deleted_count} unverified users past verification time")
        
        return deleted_count
