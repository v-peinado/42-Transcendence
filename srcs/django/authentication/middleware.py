from authentication.models import UserSession
from django.utils import timezone
import logging

# Activity Tracking Middleware for informing users of inactivity (cleanup GDPR service)

# IMPORTANT NOTE: This middleware only tracks user activity when they make requests to the server.
# Simply having a browser tab open will NOT count as activity. The user must interact with the
# application (navigate pages, make API calls, etc.) to be considered active.

# Current behavior:
# - Activity is updated only on server requests
# - Session remains valid until SESSION_COOKIE_AGE expires
# - Users are marked inactive after INACTIVITY_THRESHOLD without requests
# - Warning email sent after INACTIVITY_WARNING time
# - Account deleted after full INACTIVITY_THRESHOLD if no new activity

logger = logging.getLogger(__name__)

class UserSessionMiddleware:
    """Track user activity and update session data"""
    def __init__(self, get_response):
        """Set the get_response method"""
        self.get_response = get_response

    def __call__(self, request):
        """Run the middleware"""
        try:
            if request.user.is_authenticated:
                # counter starts from the logout moment, not from the previous activity
                self.update_user_activity(request)
        except Exception as e:
            logger.error(f"Error in UserSessionMiddleware: {str(e)}")

        response = self.get_response(request)
        return response

    def update_user_activity(self, request):
        """ Updates the user's last activity timestamp and resets inactivity notifications.
        
        This method:
        1. Gets or creates a user session record
        2. Updates the last activity timestamp
        3. Resets any inactivity notification flags when user shows activity
        """
        try:
            current_time = timezone.now() # Get current time
            session_key = request.session.session_key # Get session key (this key is a unique id for the session)

			# If session key does not exist, create a new session
            if not session_key:
                request.session.create()
                session_key = request.session.session_key

            # Get or create user session record
            session, _ = UserSession.objects.get_or_create(
                user=request.user,	# Get the user
                session_id=session_key,	# Get the session key
                defaults={'last_activity': current_time} # Set the last activity to the current time
            )
            
            if not _:  # If session already existed
                session.last_activity = current_time	# Update the last activity to the current time
                session.save(update_fields=['last_activity'])	# Save the session
                
            # Reset inactivity notification if exists
            if request.user.inactivity_notified:	# If the user has been notified of inactivity
                request.user.inactivity_notified = False	# Reset the inactivity notification
                request.user.inactivity_notification_date = None	# Reset the inactivity notification date
                request.user.save(update_fields=['inactivity_notified', 'inactivity_notification_date'])	# Save the user
                logger.info(f"Reset inactivity warning for user {request.user.username} due to activity")	# Log the reset

        except Exception as e:
            logger.error(f"Error updating user activity: {str(e)}")

# Alias for UserSessionMiddleware for consistency
UpdateLastActivityMiddleware = UserSessionMiddleware
