"""
Activity Tracking Middleware

IMPORTANT NOTE: This middleware only tracks user activity when they make requests to the server.
Simply having a browser tab open will NOT count as activity. The user must interact with the
application (navigate pages, make API calls, etc.) to be considered active.

Current behavior:
- Activity is updated only on server requests
- Session remains valid until SESSION_COOKIE_AGE expires
- Users are marked inactive after INACTIVITY_THRESHOLD without requests
- Warning email sent after INACTIVITY_WARNING time
- Account deleted after full INACTIVITY_THRESHOLD if no new activity
"""

from django.utils import timezone
from django.conf import settings
from authentication.models import UserSession
import logging

logger = logging.getLogger(__name__)

class UserSessionMiddleware:
    """Track user activity and update session data"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            if request.user.is_authenticated:
                # FIXED: DO update activity during logout so the inactivity
                # counter starts from the logout moment, not from the previous activity
                self.update_user_activity(request)
        except Exception as e:
            logger.error(f"Error in UserSessionMiddleware: {str(e)}")

        response = self.get_response(request)
        return response

    def update_user_activity(self, request):
        """
        Updates the user's last activity timestamp and resets inactivity notifications.
        
        This method:
        1. Gets or creates a user session record
        2. Updates the last activity timestamp
        3. Resets any inactivity notification flags when user shows activity
        """
        try:
            current_time = timezone.now()
            session_key = request.session.session_key

            if not session_key:
                request.session.create()
                session_key = request.session.session_key

            # Update or create session record
            session, _ = UserSession.objects.get_or_create(
                user=request.user,
                session_id=session_key,
                defaults={'last_activity': current_time}
            )
            
            if not _:  # If session already existed
                session.last_activity = current_time
                session.save(update_fields=['last_activity'])
                
            # Reset inactivity notification if exists
            if request.user.inactivity_notified:
                request.user.inactivity_notified = False
                request.user.inactivity_notification_date = None
                request.user.save(update_fields=['inactivity_notified', 'inactivity_notification_date'])
                logger.info(f"Reset inactivity warning for user {request.user.username} due to activity")

        except Exception as e:
            logger.error(f"Error updating user activity: {str(e)}")

# Alias para compatibilidad hacia atrás
UpdateLastActivityMiddleware = UserSessionMiddleware
