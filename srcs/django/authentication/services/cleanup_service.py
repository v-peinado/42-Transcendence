from authentication.models import CustomUser, UserSession
from .mail_service import MailSendingService
from .gdpr_service import GDPRService
from django.utils import timezone
from django.conf import settings
import logging


# Cleanup Service for GDPR compliance and inactive user management.

# This service handles:
# - Detection and deletion of unverified accounts past verification timeout
# - Identification of inactive users requiring notification
# - Sending of inactivity warning emails
# - Deletion of users who haven't responded to inactivity warnings
# - Respecting active user sessions and recent activity



logger = logging.getLogger(__name__)

class CleanupService:
    @classmethod
    def cleanup_inactive_users(cls, email_connection=None):
        """
        Main GDPR cleanup method that handles user inactivity management.
        
        This method:
        1. Deletes unverified accounts past verification timeout (EMAIL_VERIFICATION_TIMEOUT)
        2. Identifies users with recent activity and resets inactivity warnings
        3. Sends warnings to inactive users approaching threshold (INACTIVITY_WARNING)
        4. Deletes/anonymizes users who haven't responded to warnings after grace period (INACTIVITY_THRESHOLD)
        """
        try:
            current_time = timezone.now() # Get current time
            deleted_count = 0	# Initialize deleted count
            notification_count = 0	# Initialize notification count
            
            # 1. Clean unverified users
            cls._cleanup_unverified_users(current_time) # cls is like "self" but for class methods
            
            # 2. Get users with active sessions
            active_sessions = cls._get_active_sessions(current_time)
            
            # 3. Reset notification for users with recent activity
            cls._reset_notifications_for_active_users(active_sessions)
            
            # 4. Get base query for inactive users
            base_query = cls._get_inactive_users_base_query(active_sessions)
            
            # 5. Send notifications to inactive users
            cls._notify_inactive_users(base_query, current_time, email_connection)
            
            # 6. Process deletions for users past grace period
            cls._process_deletions(base_query, current_time)
                
        except Exception as e:
            logger.error(f"Error in cleanup_inactive_users: {str(e)}")
            raise
    
    @classmethod
    def _cleanup_unverified_users(cls, current_time):
        """Delete unverified users past verification timeout"""
        verification_threshold = current_time - timezone.timedelta(
            seconds=settings.EMAIL_VERIFICATION_TIMEOUT
        )
        
        # Exclude already anonymized users
        unverified_users = CustomUser.objects.filter(
            is_active=False,
            email_verified=False,
            date_joined__lt=verification_threshold
        ).exclude(
            username__startswith='deleted_user_'  # Exclude already processed users
        ).exclude(
            is_superuser=True
        )
        
        deleted_count = 0
        for user in unverified_users:
            logger.info(
                f"🔥 Deleting unverified user {user.username}:\n"
                f"- Registration date: {user.date_joined}\n"
                f"- Threshold date: {verification_threshold}\n" 
                f"- Current time: {current_time}"
            )
            try:
                GDPRService.delete_user_data(user)
                deleted_count += 1	# Increment deleted count
            except Exception as e:
                logger.error(f"Error deleting unverified user {user.username}: {str(e)}")
        
        # Only log if there's something to report
        if deleted_count > 0:
            logger.info(f"🧹 Deleted {deleted_count} unverified users")
    
    @classmethod
    def _get_active_sessions(cls, current_time):
        """ 
        Return a set of user IDs with active sessions.
        current_time (datetime): The current time to consider
        """
        try:
            # Query for active sessions
            active_sessions = UserSession.objects.filter(
                last_activity__gt=current_time - timezone.timedelta(seconds=settings.INACTIVITY_WARNING / 2)
            ).select_related('user')
            
            # Extract user IDs
            active_user_ids = set(session.user_id for session in active_sessions)
            
            # Log only when debugging or if there are active sessions to report
            if active_user_ids:	# If there are active sessions
                logger.info(f"Found {len(active_user_ids)} active user sessions to exclude from cleanup")
                
            return active_user_ids
        except Exception as e:
            logger.error(f"Error getting active sessions: {str(e)}")
            return set()
    
    @classmethod
    def _reset_notifications_for_active_users(cls, active_sessions):
        """Reset inactivity notification flags for users with recent activity"""
        for user_id in active_sessions: # Iterate over active sessions
            try:
                user = CustomUser.objects.get(id=user_id, inactivity_notified=True) # Get user
                user.inactivity_notified = False # Reset notification flag
                user.inactivity_notification_date = None # Reset notification date
                user.save(update_fields=['inactivity_notified', 'inactivity_notification_date']) # Save changes
                logger.info(f"Reset inactivity notification for active user: {user.username}") # Log
            except CustomUser.DoesNotExist:
                continue
    
    @classmethod
    def _get_inactive_users_base_query(cls, active_sessions):
        """Get inactive users base query excluding active users to cleanup"""
        return CustomUser.objects.filter(
            is_active=True,	# Only active users
            email_verified=True	# Only verified users
        ).exclude(
            id__in=active_sessions	# Exclude users with active sessions
        ).exclude(
            is_superuser=True	# Exclude superusers from cleanup
        )
    
    @classmethod
    def _notify_inactive_users(cls, base_query, current_time, email_connection=None):
        """put the users that need to be notified in a list"""
        users_to_notify = []	# Initialize list of users to notify
        
        for user in base_query.filter(inactivity_notified=False):	# Iterate over inactive users
            last_activity = user.get_last_activity()	# Get last activity
            
			# If the user has been inactive for more than the warning period and hasn't been notified
            if last_activity and (current_time - last_activity).total_seconds() >= settings.INACTIVITY_WARNING:
                users_to_notify.append(user)	# Add user to list of users to notify
        
        notification_count = len(users_to_notify)
        
        if notification_count > 0:
            logger.info(f"⚠️  Found {notification_count} users to warn")
            for user in users_to_notify:
                cls._send_inactivity_warning(user, current_time, email_connection)
    
    @classmethod
    def _send_inactivity_warning(cls, user, current_time, email_connection=None):
        """Send mail to user to warn about inactivity"""
        try:
            # Check if user has an email address
            if not user.email:
                logger.warning(f"No email address for user {user.username}")
                return
                
            # Calculate remaining time for warning (inactive time - warning time = period between warning and deletion)
            seconds_remaining = settings.INACTIVITY_THRESHOLD - settings.INACTIVITY_WARNING
            
            if settings.TEST_MODE == 'True':
                # In test mode, show seconds
                remaining_time = seconds_remaining
                time_unit = 'seconds'
            else:
                # In production, show days
                remaining_time = seconds_remaining / 86400	# Convert to days
                time_unit = 'days'
            
            logger.info(f"Sending inactivity warning to {user.username}. Time remaining: {remaining_time} {time_unit}")
            
            MailSendingService.send_inactivity_warning(
                user, 
                remaining_days=remaining_time,
                time_unit=time_unit,
                connection=email_connection
            )
            user.inactivity_notified = True
            user.inactivity_notification_date = current_time
            user.save()
            logger.info(f"📧 Warning sent to: {user.username}")
        except Exception as e:
            logger.error(f"Error sending warning to {user.username}: {str(e)}")
    
    @classmethod
    def _process_deletions(cls, base_query, current_time):
        """Process deletions for users past grace period"""
        
		# Calculate warning expiry date (current time - grace period)
        warning_expiry = current_time - timezone.timedelta(
            seconds=settings.INACTIVITY_WARNING
        )
        
		# Get users to delete
        inactive_users = base_query.filter(
            inactivity_notified=True, # Users who have been notified
            inactivity_notification_date__lt=warning_expiry	# Users who have been notified before the grace period
        )
        
		# If there are users to delete...
        if inactive_users.exists():
            logger.info(f"🗑️  Found {inactive_users.count()} users to delete")
            for user in inactive_users:
                cls._process_user_deletion(user, current_time) # ...process deletion
    
    @classmethod
    def _process_user_deletion(cls, user, current_time):
        """Process deletion for a specific user"""
        
		# Get last activity and calculate inactivity time for logging
        last_activity = user.get_last_activity() # Get last activity
        inactivity_time = (current_time - last_activity).total_seconds() # Calculate inactivity time
        notification_age = (current_time - user.inactivity_notification_date).total_seconds() # Calculate notification age
        
        logger.info(
            f"❌ Checking deletion for {user.username}:\n"
            f"- Joined: {user.date_joined}\n"
            f"- Last login: {user.last_login}\n" 
            f"- Last activity: {last_activity}\n"
            f"- Inactivity time: {inactivity_time} seconds\n"
            f"- Notified at: {user.inactivity_notification_date}\n"
            f"- Notification age: {notification_age} seconds\n"
            f"- Current time: {current_time}"
        )
        
        # Deletion condition: Notification was sent and grace period has passed
        if notification_age >= settings.INACTIVITY_WARNING:
            try:
                deleted_username = user.username
                GDPRService.delete_user_data(user)
                logger.info(f"🗑️  Deleted user {deleted_username}")
            except Exception as e:
                logger.error(f"Error deleting user {user.username}: {str(e)}")
