from django.core.exceptions import ValidationError
from authentication.models import CustomUser
from .mail_service import MailSendingService
from .token_service import TokenService
from .password_service import PasswordService
from .two_factor_service import TwoFactorService
from authentication.forms.auth_forms import RegistrationForm
from django.contrib.auth import authenticate, login as auth_login, logout
from django.utils.html import escape
from authentication.models import PreviousPassword
from .rate_limit_service import RateLimitService
import logging

logger = logging.getLogger(__name__)

class AuthenticationService:
    MESSAGES = {
        "privacy_policy": "You must accept the privacy policy",
        "email_verification": "email_verification_required",
        "form_validation": "Form validation error",
        "logout_success": "Successfully logged out",
        "no_session": "No active session",
    }

    @staticmethod
    def register_user(username, email, password):
        """Basic user registration"""
        # The mail will be encrypted in the save() method
        user = CustomUser.objects.create_user(
            username=username.lower(),
            email=email.lower(),  # It will be encrypted in the save() method
            password=password,
            is_active=False,
        )
        return user

    @staticmethod
    def login_user(request, username, password, remember=False):
        """
        Manages the login process
        Includes rate limiting and 2FA validation
        Returns: 'verify_2fa' if 2FA is enabled, 'user' if login successful
        """
        rate_limiter = RateLimitService()
        ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        # Check rate limiting
        is_limited, remaining_time = rate_limiter.is_rate_limited(ip, 'login')
        if is_limited:
            logger.warning(f"Rate limit exceeded for IP {ip} on login")
            raise ValidationError(f"Demasiados intentos. Por favor espera {remaining_time} segundos")

        user = authenticate(request, username=username.strip().lower(), password=password)

        if not user:
            logger.warning(f"Failed login attempt for user {username} from IP {ip}")
            raise ValidationError("Usuario o contraseña incorrectos")

        if not user.email_verified:
            raise ValidationError("Por favor verifica tu email para activar tu cuenta")

        # Reset rate limit on successful login
        rate_limiter.reset_limit(ip, 'login')

        if user.two_factor_enabled:
            request.session.update(
                {
                    "pending_user_id": user.id,
                    "user_authenticated": True,
                    "manual_user": True,
                }
            )

            code = TwoFactorService.generate_2fa_code(user)
            TwoFactorService.send_2fa_code(user, code)
            return "verify_2fa"

        auth_login(request, user)
        if not remember:
            request.session.set_expiry(0)

        return "user"

    @staticmethod
    def handle_registration(form_data):
        """
        Manages the complete registration process
        Includes form validation, user creation and email verification
        """
        if not form_data.get("privacy_policy"):
            raise ValidationError(AuthenticationService.MESSAGES["privacy_policy"])

        username = escape(form_data.get("username", "").strip())
        email = escape(form_data.get("email", "").strip())
        password = form_data.get("password1")
        confirm_password = form_data.get("password2")

        # Data validation
        PasswordService.validate_manual_registration(
            username, email, password, confirm_password
        )

        form = RegistrationForm(form_data)
        if form.is_valid():
            # User registration
            user = AuthenticationService.register_user(
                form.cleaned_data["username"],
                form.cleaned_data["email"],
                form.cleaned_data["password1"],
            )

            # Save previous password
            PreviousPassword.objects.create(user=user, password=user.password)

            # Generate and send email verification token
            token = TokenService.generate_email_verification_token(user)
            MailSendingService.send_verification_email(user, token)
            return True

        return False

    @staticmethod
    def logout_user(request):
        """
        Logs out the current user
        Raises ValidationError if no user is authenticated
        """
        if request.user.is_authenticated:
            logout(request)
            # Clear session ressidue data
            request.session.flush()
            return True
        raise ValidationError(AuthenticationService.MESSAGES["no_session"])
