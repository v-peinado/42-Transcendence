from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
import logging
import hashlib
from authentication.models import CustomUser, UserSession 
from .mail_service import MailSendingService

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
            
            # Generate new hash for anonymized email
            anon_email_hash = hashlib.sha256(anon_email.encode()).hexdigest()

            # Save anonymous data
            user.username = anon_username
            user.email = anon_email
            user.email_hash = anon_email_hash  # Assuming you have this field
            user.first_name = "Deleted"
            user.last_name = "User"
            user.profile_image = None
            user.fortytwo_image = None
            user.is_active = False
            user.two_factor_enabled = False
            user.two_factor_secret = None
            user.deleted_at = timezone.now()
            user.save()

            return True
        except Exception as e:
            raise ValidationError(f"Error anonymizing user: {str(e)}")

    @staticmethod
    def delete_user_data(user):
        """Soft deletes user's account by anonymizing their data"""
        try:
            # Now we just call anonymize_user
            GDPRService.anonymize_user(user)
            return True
        except Exception as e:
            raise ValidationError(f"Error deleting user: {str(e)}")

    @classmethod
    def cleanup_inactive_users(cls, email_connection=None):
        try:
            current_time = timezone.now()
            
            # Modify queries to exclude already deleted users
            base_query = CustomUser.objects.filter(deleted_at__isnull=True)
            
            # 1. Clean unverified users
            verification_threshold = current_time - timezone.timedelta(
                seconds=settings.EMAIL_VERIFICATION_TIMEOUT
            )
            
            unverified_users = base_query.filter(
                is_active=False,
                email_verified=False,
                date_joined__lt=verification_threshold
            ).exclude(is_superuser=True)

            for user in unverified_users:
                logger.info(
                    f"Deleting unverified user {user.username}:\n"
                    f"- Joined date: {user.date_joined}\n"
                    f"- Current time: {current_time}"
                )
                cls.delete_user_data(user)  # Using the existing delete_user_data method

            # 2. Process inactive verified users
            active_sessions = UserSession.objects.filter(
                last_activity__gt=current_time - timezone.timedelta(seconds=settings.INACTIVITY_THRESHOLD)
            ).values_list('user_id', flat=True).distinct()

            logger.info(f"Found {len(active_sessions)} active user sessions to exclude from cleanup")

            # Base queryset excluding active users
            base_query = base_query.exclude(
                id__in=active_sessions
            ).exclude(
                is_superuser=True
            ).filter(
                is_active=True,
                email_verified=True
            )

            # 3. Notify users approaching inactivity threshold
            warning_threshold = current_time - timezone.timedelta(
                seconds=settings.INACTIVITY_THRESHOLD - settings.INACTIVITY_WARNING
            )
            
            users_to_notify = base_query.filter(
                last_login__lt=warning_threshold,
                inactivity_notified=False
            )

            for user in users_to_notify:
                logger.info(f"Sending inactivity warning to user {user.username}")
                MailSendingService.send_inactivity_warning(user, connection=email_connection)
                user.inactivity_notified = True
                user.inactivity_notification_date = current_time
                user.save()

            # 4. Delete inactive users who were notified and warning period expired
            deletion_threshold = current_time - timezone.timedelta(
                seconds=settings.INACTIVITY_THRESHOLD
            )
            warning_expiry = current_time - timezone.timedelta(
                seconds=settings.INACTIVITY_WARNING
            )

            inactive_users = base_query.filter(
                last_login__lt=deletion_threshold,
                inactivity_notified=True,
                inactivity_notification_date__lt=warning_expiry
            )

            # Double check for active sessions before deletion
            inactive_users = inactive_users.exclude(
                id__in=UserSession.objects.filter(
                    last_activity__gt=deletion_threshold
                ).values_list('user_id', flat=True)
            )

            logger.info(f"Found {inactive_users.count()} users to delete")
            for user in inactive_users:
                logger.info(
                    f"Deleting user {user.username}:\n"
                    f"- Last login: {user.last_login}\n"
                    f"- Notification date: {user.inactivity_notification_date}\n"
                    f"- Current time: {current_time}"
                )
                cls.delete_user_data(user)

        except Exception as e:
            logger.error(f"Error in cleanup_inactive_users: {str(e)}")
            raise
