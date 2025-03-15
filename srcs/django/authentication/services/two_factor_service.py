from django.template.loader import render_to_string
from datetime import datetime, timedelta
from django.utils.html import strip_tags
from django.core.mail import send_mail
from .rate_limit_service import RateLimitService
from django.utils import timezone
from django.conf import settings
from ..models import CustomUser
import secrets
import logging
import random
import jwt

logger = logging.getLogger(__name__)

class TwoFactorService:
    @staticmethod
    def _check_rate_limit(user_id, action='two_factor'):
        """Check rate limiting for 2FA operations"""
        rate_limiter = RateLimitService()
        is_limited, remaining_time = rate_limiter.is_rate_limited(user_id, action)
        
        if is_limited:
            logger.warning(f"Rate limit exceeded for user {user_id} on {action}")
            raise ValueError(f"Demasiados intentos. Por favor, espera {remaining_time} segundos.")
        
        return rate_limiter
    
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

            # Check rate limiting before generating a code
            user_id = user.id
            rate_limiter = TwoFactorService._check_rate_limit(user_id)
                
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
            
            # Reset rate limit after successful code generation
            rate_limiter.reset_limit(user_id, 'two_factor')
            logger.info(f"2FA code generated for user {user_id}")
            
            return code

        except ValueError as e:
            # Re-raise ValueError for rate limiting
            raise e
        except Exception as e:
            logger.error(f"Error generating 2FA code: {str(e)}")
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
            # Rate limiting check for verification attempts
            user_id = user.id
            TwoFactorService._check_rate_limit(user_id)
            
            if not user.two_factor_secret or not code:
                return False

            # Check expiration time
            time_diff = timezone.now() - user.last_2fa_time
            if time_diff.total_seconds() > 300:  # 5 minutes
                return False

            result = user.last_2fa_code == code
            
            # If verification is successful, reset the rate limit
            if result:
                rate_limiter = RateLimitService()
                rate_limiter.reset_limit(user_id, 'two_factor')
                logger.info(f"2FA code verified successfully for user {user_id}")
                
            return result

        except ValueError:
            # Rate limiting error
            return False
        except Exception:
            logger.error(f"Error verifying 2FA code for user {user.id}")
            return False

    @staticmethod
    def send_2fa_code(user, code):
        """Sends the 2FA code via email"""
        try:
            # Check rate limiting before sending email
            user_id = user.id
            TwoFactorService._check_rate_limit(user_id, 'email_send')
            
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
            
            logger.info(f"2FA code sent to user {user_id}")
            return True
            
        except ValueError as e:
            # Re-raise ValueError for rate limiting
            raise e
        except Exception as e:
            logger.error(f"Error sending 2FA code: {str(e)}")
            raise ValueError(f"Error al enviar código 2FA: {str(e)}")

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
