from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from ..models import CustomUser
from .mail_service import MailSendingService
import logging

logger = logging.getLogger(__name__)

class GDPRService:
    @staticmethod
    def export_user_data(user):
        """Exports all user's personal data in dictionary format"""
        return {
            "personal_info": {
                "username": user.username,
                "email": user.email,
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
            anon_email = f"deleted_{user.id}@anonymous.com"

            # Save anonymous data to user after deleting sensitive data
            user.username = anon_username
            user.email = anon_email
            user.first_name = "Deleted"
            user.last_name = "User"
            user.profile_image = None
            user.fortytwo_image = None
            user.is_active = False
            user.two_factor_enabled = False
            user.two_factor_secret = None
            user.save()

            return True
        except Exception as e:
            raise ValidationError(f"Error al anonimizar usuario: {str(e)}")

    @staticmethod
    def delete_user_data(user):
        """Permanently deletes user's account"""
        try:
            # First anonymize user data
            GDPRService.anonymize_user(user)
            # Then delete user
            user.delete()
            return True
        except Exception as e:
            raise ValidationError(f"Error al eliminar usuario: {str(e)}")

    @staticmethod
    def cleanup_inactive_users():
        """
        Cleanup inactive users based on configured thresholds
        """
        try:
            # Cleanup unverified users
            unverified_threshold = timezone.now() - timezone.timedelta(hours=settings.EMAIL_VERIFICATION_TIMEOUT_HOURS)
            unverified_users = CustomUser.objects.filter(
                email_verified=False,
                date_joined__lt=unverified_threshold
            )
            
            for user in unverified_users:
                logger.info(f"Deleting unverified user {user.username} registered at {user.date_joined}")
                GDPRService.delete_user_data(user)

            # Notify users approaching inactivity threshold
            users_to_notify = CustomUser.objects.filter(
                is_active=True,
                email_verified=True,
                inactivity_notified=False,
                last_login__lt=timezone.now() - timezone.timedelta(days=settings.INACTIVITY_THRESHOLD_DAYS - settings.INACTIVITY_WARNING_DAYS)
            )

            for user in users_to_notify:
                if user.should_notify_inactivity():
                    logger.info(f"Sending inactivity warning to user {user.username}")
                    MailSendingService.send_inactivity_warning(user)
                    user.inactivity_notified = True
                    user.inactivity_notification_date = timezone.now()
                    user.save()

            # Delete inactive users
            inactive_threshold = timezone.now() - timezone.timedelta(days=settings.INACTIVITY_THRESHOLD_DAYS)
            inactive_users = CustomUser.objects.filter(
                is_active=True,
                last_login__lt=inactive_threshold,
                inactivity_notified=True,
                inactivity_notification_date__lt=timezone.now() - timezone.timedelta(days=settings.INACTIVITY_WARNING_DAYS)
            )

            for user in inactive_users:
                if user.is_inactive_for_too_long():
                    logger.info(f"Deleting inactive user {user.username}, last login: {user.last_login}")
                    GDPRService.delete_user_data(user)

        except Exception as e:
            logger.error(f"Error in cleanup_inactive_users: {str(e)}")
            raise
