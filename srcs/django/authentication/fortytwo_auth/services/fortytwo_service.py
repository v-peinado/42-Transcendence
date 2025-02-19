import requests
from django.conf import settings
from authentication.services.token_service import TokenService
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from authentication.services.mail_service import MailSendingService
from authentication.services.two_factor_service import TwoFactorService
from authentication.models import CustomUser
from django.contrib.auth import login as auth_login
from django.utils import timezone
from datetime import timedelta
from authentication.services.rate_limit_service import RateLimitService
import logging

logger = logging.getLogger(__name__)


class FortyTwoAuthService:
    AUTH_URL = "https://api.intra.42.fr/oauth/authorize"
    TOKEN_URL = "https://api.intra.42.fr/oauth/token"
    USER_URL = "https://api.intra.42.fr/v2/me"

    def __init__(self, is_api=False):
        self.is_api = is_api
        if is_api:
            self.client_id = settings.FORTYTWO_API_UID
            self.client_secret = settings.FORTYTWO_API_SECRET
            self.redirect_uri = settings.FORTYTWO_API_URL
        else:
            self.client_id = settings.FORTYTWO_CLIENT_ID
            self.client_secret = settings.FORTYTWO_CLIENT_SECRET
            self.redirect_uri = settings.FORTYTWO_REDIRECT_URI
        self.rate_limiter = RateLimitService()
        self.TOKEN_EXPIRY_HOURS = 24

    @classmethod
    def get_auth_url(cls, is_api=False):
        service = cls(is_api=is_api)
        params = {
            "client_id": service.client_id,
            "redirect_uri": service.redirect_uri,
            "response_type": "code",
            "scope": "public",
        }
        return f"{cls.AUTH_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"

    def _make_request(self, method, url, **kwargs):
        response = requests.request(method, url, **kwargs)
        if response.status_code != 200:
            raise Exception(f"API request failed: {response.text}")
        return response.json()

    def get_access_token(self, code):
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        return self._make_request("POST", self.TOKEN_URL, data=data)

    def get_user_info(self, access_token):
        headers = {"Authorization": f"Bearer {access_token}"}
        return self._make_request("GET", self.USER_URL, headers=headers)

    def process_user_authentication(self, user_data):
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
        try:
            auth_url = cls.get_auth_url(is_api=is_api)
            return True, auth_url, None
        except Exception as e:
            return False, None, str(e)

    @classmethod
    def handle_callback(cls, request, is_api=False, code=None):
        code = code or request.GET.get("code")
        if not code:
            return False, None, "No se proporcionó código de autorización"

        # Rate limiting check
        service = cls(is_api=is_api)
        ip = request.META.get("REMOTE_ADDR", "unknown")
        is_limited, remaining_time = service.rate_limiter.is_rate_limited(
            ip, "oauth_callback"
        )

        if is_limited:
            logger.warning(f"Rate limit exceeded for IP {ip}")
            return (
                False,
                None,
                f"Too many attempts. Please try again in {remaining_time} seconds",
            )

        try:
            token_data = service.get_access_token(code)
            user_data = service.get_user_info(token_data["access_token"])
            user, created = service.process_user_authentication(user_data)

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
