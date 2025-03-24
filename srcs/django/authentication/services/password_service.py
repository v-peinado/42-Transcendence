from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ValidationError
from ..models import PreviousPassword, CustomUser
from .rate_limit_service import RateLimitService
from .mail_service import MailSendingService
from authentication.models import CustomUser
from .token_service import TokenService
from django.utils.html import escape
import logging
import re

logger = logging.getLogger(__name__)

class PasswordService:
    @staticmethod
    def _validate_password_match(password1, password2):
        if password1 != password2:
            raise ValidationError("Las contraseñas no coinciden")

    @staticmethod
    def _validate_password_complexity(password, user):
        if password.lower() == user.username.lower():
            raise ValidationError(
                "La contraseña no puede ser igual al nombre de usuario"
            )

        if not all(char.isprintable() for char in password):
            raise ValidationError(
                "La contraseña no puede contener caracteres no imprimibles"
            )

        min_length, max_length = 8, 20
        if len(password) < min_length:
            raise ValidationError(
                f"La contraseña debe tener al menos {min_length} caracteres"
            )
        if len(password) > max_length:
            raise ValidationError(
                f"La contraseña no puede tener más de {max_length} caracteres"
            )

        validate_password(password, user)

    @staticmethod
    def _validate_password_history(user, password):
        """Check if password has been used before"""
        if user.pk:
            previous_passwords = PreviousPassword.objects.filter(user=user).order_by(
                "-created_at"
            )[:3]
            for prev_password in previous_passwords:
                if check_password(password, prev_password.password):
                    raise ValidationError(
                        "No puedes reutilizar ninguna de tus últimas tres contraseñas"
                    )

    @staticmethod
    def _validate_password_basic(user, password1, password2):
        """Validate password complexity and history"""
        PasswordService._validate_password_match(password1, password2)
        PasswordService._validate_password_complexity(password1, user)
        PasswordService._validate_password_history(user, password1)

    @staticmethod
    def validate_password_change(user, current_password, new_password1, new_password2):
        """Validate password change request"""
        if not user.check_password(current_password):
            raise ValidationError("La contraseña actual es incorrecta")
        PasswordService._validate_password_basic(user, new_password1, new_password2)

    @staticmethod
    def validate_manual_registration(username, email, password1, password2):
        """Validar datos de registro con protección contra XSS y SQL injection"""

        # Escape html characters to prevent XSS attacks
        username = escape(username)
        email = escape(email)

        dangerous_patterns = [
            "<script>", "javascript:", "onerror=", "onload=", "onclick=", "data:", "alert(", "eval(",  # XSS
            "SELECT", "UNION", "--",  # SQL Injection
            "../", "..\\",  # Path Traversal
            "&", "|", ";", "`", "$", "(", ")", "{", "}",  # Command Injection
            "\0", "\n", "\r", "\t", "\b",  # Control Characters
        ]
        allowed_chars = ["-", ".", "_", "@", "+"]

        # Validate against dangerous patterns
        for pattern in dangerous_patterns:
            if pattern in username.lower() or pattern in email.lower():
                raise ValidationError(
                    f"Caracteres no permitidos detectados en '{username if pattern in username.lower() else email}'"
                )

        # Verify that only allowed characters are used
        if not all(char.isalnum() or char in allowed_chars for char in username):
            raise ValidationError(
                "Solo se permiten letras, números y los caracteres: - . _ @ +"
            )

        # Validate email format
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            raise ValidationError(f"Formato de email '{email}' no válido")

        # Verify if username is already taken
        if CustomUser.objects.filter(username=username.lower()).exists():
            raise ValidationError(f"El nombre de usuario '{username}' ya está en uso")

        # Verify if email is already taken using hash comparison
        temp_user = CustomUser(email=email.lower())
        email_hash = temp_user._generate_email_hash(email.lower())
        if CustomUser.objects.filter(email_hash=email_hash).exists():
            raise ValidationError(f"El email '{email}' ya está registrado")

        # Validate length of username
        max_length_username = 10
        if len(username) > max_length_username:
            raise ValidationError(
                f"El nombre de usuario no puede tener más de {max_length_username} caracteres"
            )

        # Validate 42. prefix
        if username.startswith("42."):
            raise ValidationError("El prefijo '42.' está reservado para usuarios de 42")

        # Validate 42 email domain
        if re.match(r".*@student\.42.*\.com$", email.lower()):
            raise ValidationError(
                "Los correos con dominio @student.42*.com están reservados para usuarios de 42"
            )

        PasswordService._validate_password_basic(
            CustomUser(username=username), password1, password2
        )

    @staticmethod
    def initiate_password_reset(email):
        """Iniciate password reset process"""
        rate_limiter = RateLimitService()
        
        if re.match(r".*@student\.42.*\.com$", email.lower()):
            raise ValidationError(
                "Los usuarios de 42 deben iniciar sesión a través del botón de login de 42")

        # Create a hash of the email to compare with the database
        temp_user = CustomUser(email=email.lower())
        email_hash = temp_user._generate_email_hash(email.lower())
        
        # search for the user with the email hash
        users = CustomUser.objects.filter(
            email_hash=email_hash, is_active=True, is_fortytwo_user=False)

        if not users.exists():
            return False

        user = users.first()
        if user.is_fortytwo_user:
            raise ValidationError("Los usuarios de 42 no pueden usar esta función")
            
        # Verify rate limit for password_reset attempts
        is_limited, remaining_time = rate_limiter.is_rate_limited(
            email.lower(), 'password_reset')
            
        if is_limited:
            logger.warning(f"Rate limit exceeded for email {email} on password reset")
            raise ValidationError(f"Demasiados intentos. Por favor, espera {remaining_time} segundos e inténtalo de nuevo.")

        try:
            token_data = TokenService.generate_password_reset_token(user)
            MailSendingService.send_password_reset_email(user, token_data)
            return token_data
        except ValidationError as e:
            raise e # Propagate validation errors to the view

    @staticmethod
    def confirm_password_reset(uidb64, token, new_password1, new_password2):
        """Password reset confirmation"""
        try:
            user = TokenService.verify_password_reset_token(uidb64, token)

            PasswordService._validate_password_basic(user, new_password1, new_password2)

            user.set_password(new_password1)
            user.save()
            PreviousPassword.objects.create(user=user, password=user.password)
            MailSendingService.send_password_changed_notification(user, is_reset=True)
            return True

        except ValidationError as e:
            raise ValidationError(str(e))
        except Exception as e:
            raise ValidationError(f"Error inesperado: {str(e)}")
