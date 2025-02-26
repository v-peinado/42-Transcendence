"""
Activity Tracking Middleware

IMPORTANT NOTE: This middleware only tracks user activity when they make requests to the server.
Simply having a browser tab open will NOT count as activity. The user must interact with the
application (navigate pages, make API calls, etc.) to be considered active.

To implement true "presence" detection, you would need to:
1. Implement a frontend heartbeat mechanism using WebSocket or periodic API calls
2. Add client-side activity detection (mouse movement, keyboard input, etc.)
3. Send periodic updates to the server even when the user is just viewing content

Current behavior:
- Activity is updated only on server requests
- Session remains valid until SESSION_COOKIE_AGE expires
- Users are marked inactive after INACTIVITY_THRESHOLD without requests
- Warning email sent after (INACTIVITY_THRESHOLD - INACTIVITY_WARNING) time
- Account deleted after INACTIVITY_THRESHOLD if no new activity
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
            if request.user.is_authenticated and not request.path.endswith('/delete-account/'):
                UserSession.objects.update_or_create(
                    user=request.user,
                    defaults={
                        'last_activity': timezone.now(),
                        'session_id': request.session.session_key
                    }
                )
        except Exception as e:
            logger.error(f"Error in UserSessionMiddleware: {str(e)}")

        response = self.get_response(request)
        return response

UpdateLastActivityMiddleware = UserSessionMiddleware
