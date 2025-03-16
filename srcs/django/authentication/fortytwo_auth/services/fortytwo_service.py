from authentication.services.rate_limit_service import RateLimitService
from authentication.services.two_factor_service import TwoFactorService
from authentication.services.mail_service import MailSendingService
from authentication.services.token_service import TokenService
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth import login as auth_login
from django.utils.encoding import force_bytes
from authentication.models import CustomUser
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import requests
import logging

# FortyTwoAuthService class to handle 42 authentication

# This class is used to authenticate users using the 42 OAuth API
# It provides methods to generate the authentication URL, get the access token, and get user information
# it also handles the user authentication process and sends verification emails

logger = logging.getLogger(__name__)

class FortyTwoAuthService:
    
    AUTH_URL = "https://api.intra.42.fr/oauth/authorize" # URL to authorize the app
    TOKEN_URL = "https://api.intra.42.fr/oauth/token" # URL to get the access token
    USER_URL = "https://api.intra.42.fr/v2/me" # URL to get user information

    def __init__(self, is_api=False):
        self.is_api = is_api
        if is_api: # Check if the app is in API mode
            self.client_id = settings.FORTYTWO_API_UID # client ID
            self.client_secret = settings.FORTYTWO_API_SECRET # client secret
            self.redirect_uri = settings.FORTYTWO_API_URL # redirect URI
        else: # This ies for the development frontend of the 8000 port (deprecated)
            self.client_id = settings.FORTYTWO_CLIENT_ID
            self.client_secret = settings.FORTYTWO_CLIENT_SECRET
            self.redirect_uri = settings.FORTYTWO_REDIRECT_URI
        self.rate_limiter = RateLimitService() # Rate limit service
        self.TOKEN_EXPIRY_HOURS = 24

    @classmethod # class method is used to create a factory method that returns an instance of the class to the caller
    def get_auth_url(cls, is_api=False):
        """ Generate the authentication URL """
        service = cls(is_api=is_api)
        params = {
            "client_id": service.client_id,
            "redirect_uri": service.redirect_uri,
            "response_type": "code",
            "scope": "public",
        }
        # URL with the parameters: client_id, redirect_uri, response_type, and scope
        return f"{cls.AUTH_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"

    def _make_request(self, method, url, **kwargs):
        """ Make a request to the API to get the code, access token, or user information """
        response = requests.request(method, url, **kwargs)
        if response.status_code != 200:
            raise Exception(f"API request failed: {response.text}")
        return response.json()

    def get_access_token(self, code):
        """ Get the access token using the authorization code """
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        return self._make_request("POST", self.TOKEN_URL, data=data)

    def get_user_info(self, access_token):
        """ Get user information using the access token """
        headers = {"Authorization": f"Bearer {access_token}"}
        return self._make_request("GET", self.USER_URL, headers=headers)

    def process_user_authentication(self, user_data):
        """ Process the user authentication and form the user object """
        user, created = CustomUser.objects.get_or_create(
            username=f"42.{user_data['login']}",
            defaults={
                "email": user_data["email"],
                "fortytwo_id": str(user_data["id"]),
                "is_fortytwo_user": True,
                "is_active": False,
                "email_verified": False,
                "fortytwo_image": user_data.get("image", {}).get("link"),
            },
        )

        if created:
            self._handle_new_user(user)  # Sends verification email

        return user, created

    def _is_token_expired(self, user):
        """Check if verification token has expired"""
        if not user.email_token_created_at:
            return True
        expiry_time = user.email_token_created_at + timedelta(
            hours=self.TOKEN_EXPIRY_HOURS
        )
        return timezone.now() > expiry_time

    def _handle_new_user(self, user):
        """Generate and send a new verification token"""
        token = TokenService.generate_auth_token(user)
        user.email_verification_token = token
        user.email_token_created_at = timezone.now()
        user.save()

        MailSendingService.send_verification_email(
            user,
            {
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "token": token,
                "expiry_hours": self.TOKEN_EXPIRY_HOURS,
            },
        )

    @classmethod
    def handle_login(cls, request, is_api=False):
        """Handle the login process"""
        try:
            auth_url = cls.get_auth_url(is_api=is_api)
            return True, auth_url, None
        except Exception as e:
            return False, None, str(e)

    @classmethod
    def handle_callback(cls, request, is_api=False, code=None):
        """Handle the callback from the 42 API 
        (final step of the authentication process)"""
        
		# Get the code from the request
        code = code or request.GET.get("code")
        if not code:
            return False, None, "Invalid code"

        # Rate limiting check
        service = cls(is_api=is_api)
        ip = request.META.get("REMOTE_ADDR", "unknown")
        is_limited, remaining_time = service.rate_limiter.is_rate_limited(
            ip, "oauth_callback"
        )

        if is_limited: # If the rate limit is exceeded
            logger.warning(f"Rate limit exceeded for IP {ip}")
            return (
                False,
                None,
                f"Too many attempts. Please try again in {remaining_time} seconds",
            )

        try:
            token_data = service.get_access_token(code) # Get the access token
            user_data = service.get_user_info(token_data["access_token"]) # Get the user information
            user, created = service.process_user_authentication(user_data) # Process the user authentication

            # Reset rate limit on successful authentication
            service.rate_limiter.reset_limit(ip, "oauth_callback")

            # Check token expiration for existing users
            if (
                not created
                and not user.email_verified
                and service._is_token_expired(user)
            ):
                service._handle_new_user(user)  # Generate new token
                return (
                    False,
                    user,
                    {
                        "status": "token_expired",
                        "message": "Verification token expired. A new one has been sent.",
                    },
                )

            # Verify email first
            if created or not user.email_verified:
                return (
                    False,
                    user,
                    {
                        "status": "pending_verification",
                        "message": "Por favor, verifica tu email para continuar.",
                    },
                )

            # If 2FA is enabled, generate and send code
            if user.two_factor_enabled:
                code = TwoFactorService.generate_2fa_code(user)
                TwoFactorService.send_2fa_code(user, code)
                request.session.update(
                    {
                        "pending_user_id": user.id,
                        "user_authenticated": True,
                        "fortytwo_user": True,
                    }
                )
                return True, user, "pending_2fa"

            # If everything is OK, perform login
            auth_login(request, user)
            return True, user, None

        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return False, None, str(e)
