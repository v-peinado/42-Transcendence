from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from django.utils import timezone
from ..models import CustomUser
import jwt
from datetime import datetime, timedelta
import secrets
import random


class TwoFactorService:
    @staticmethod
    def generate_2fa_code(user):
        """Generates a temporary 2FA code using JWT"""
        try:
            # Check if user is valid
            if not user:
                raise ValueError("Usuario no proporcionado")

            # If we get an ID instead of a user object
            if not isinstance(user, CustomUser):
                try:
                    user = CustomUser.objects.get(id=user)
                except CustomUser.DoesNotExist:
                    raise ValueError("Usuario no encontrado")

            # Generate 6-digit 2FA code
            code = str(random.randint(100000, 999999))

            # Create JWT payload
            payload = {
                "user_id": user.id,
                "code": code,
                "exp": datetime.utcnow() + timedelta(minutes=5),
                "iat": datetime.utcnow(),
                "type": "2fa",
            }

            # Generate JWT token
            token = jwt.encode(
                payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
            )

            # Save code and timestamp
            user.last_2fa_code = code
            user.last_2fa_time = timezone.now()
            user.save()

            return code

        except Exception as e:
            raise ValueError(f"Error al generar código 2FA: {str(e)}")

    @staticmethod
    def verify_2fa_code(user, code):
        """Verifies if the 2FA code is valid using JWT"""
        # Verify that user is a CustomUser object
        if not isinstance(user, CustomUser):
            try:
                user = CustomUser.objects.get(id=user)
            except (ValueError, CustomUser.DoesNotExist):
                return False
        try:
            if not user.two_factor_secret or not code:
                return False

            # Check expiration time
            time_diff = timezone.now() - user.last_2fa_time
            if time_diff.total_seconds() > 300:  # 5 minutes
                return False

            return user.last_2fa_code == code

        except Exception:
            return False

    @staticmethod
    def send_2fa_code(user, code):
        """Sends the 2FA code via email"""
        subject = "Tu código de verificación PongOrama"
        context = {"user": user, "code": code}
        html_message = render_to_string("authentication/2fa_email.html", context)

        send_mail(
            subject,
            strip_tags(html_message),
            settings.DEFAULT_FROM_EMAIL,
            [user.decrypted_email],
            html_message=html_message,
            fail_silently=False,
        )

    @staticmethod
    def enable_2fa(user):
        """Enables 2FA for a user"""
        try:
            user.two_factor_secret = secrets.token_hex(16)

            user.two_factor_enabled = True
            user.save()

            return True

        except Exception as e:
            raise ValueError(f"Error al activar 2FA: {str(e)}")

    @staticmethod
    def disable_2fa(user):
        """Disables 2FA for a user"""
        user.two_factor_enabled = False
        user.two_factor_secret = None
        user.save()
        return True

    @staticmethod
    def verify_session(user_id, user_authenticated):
        """Verifies the validity of the session for 2FA"""
        try:
            if not user_id or not user_authenticated:
                return False, None

            user = CustomUser.objects.get(id=user_id)
            if not user.two_factor_enabled:
                return False, None

            return True, user

        except CustomUser.DoesNotExist:
            return False, None
        except Exception:
            return False, None

    @staticmethod
    def clean_session_keys(session):
        """Cleans session keys related to 2FA"""
        keys_to_remove = [
            "pending_user_id",
            "user_authenticated",
            "fortytwo_user",
            "manual_user",
        ]

        for key in keys_to_remove:
            if key in session:
                del session[key]
