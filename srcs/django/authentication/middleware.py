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
from authentication.models import UserSession, CustomUser

class UpdateLastActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        if request.user.is_authenticated and request.session.session_key:
            current_time = timezone.now()
            
            # Always update session activity to keep it active
            UserSession.objects.update_or_create(
                user=request.user,
                session_id=request.session.session_key,
                defaults={'last_activity': current_time}
            )

            # Also update user's last activity and reset inactivity flags
            CustomUser.objects.filter(id=request.user.id).update(
                last_login=current_time,
                inactivity_notified=False,
                inactivity_notification_date=None
            )
        
        return response
