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


class AuthenticationService:
    MESSAGES = {
        "privacy_policy": "Debes aceptar la política de privacidad",
        "email_verification": "email_verification_required",
        "form_validation": "Error en la validación del formulario",
        "logout_success": "Sesión cerrada correctamente",
        "no_session": "No hay sesión activa",
    }

    @staticmethod
    def register_user(username, email, password):
        """Basic user registration"""
        user = CustomUser.objects.create_user(
            username=username.lower(),
            email=email.lower(),
            password=password,
            is_active=False,
        )
        return user

    @staticmethod
    def login_user(request, username, password, remember=False):
        """Manages the login process"""
        user = authenticate(
            request, username=username.strip().lower(), password=password
        )

        if not user:
            raise ValidationError("Usuario o contraseña incorrectos")

        if not user.email_verified:
            raise ValidationError("Por favor verifica tu email para activar tu cuenta")

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
        """Manages the registration process"""
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

        Args:
            request: HttpRequest object

        Raises:
            ValidationError: If no user is authenticated
        """
        if request.user.is_authenticated:
            logout(request)
            return True
        raise ValidationError(AuthenticationService.MESSAGES["no_session"])
