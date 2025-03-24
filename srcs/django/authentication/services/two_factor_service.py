from django.template.loader import render_to_string
from .rate_limit_service import RateLimitService
from datetime import datetime, timedelta
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from ..models import CustomUser
import secrets
import logging
import random

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
        """Generates a temporary 2FA code"""
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
            
            # Save code and time to user object
            user.last_2fa_code = code
            user.last_2fa_time = timezone.now()
            user.save(update_fields=['last_2fa_code', 'last_2fa_time'])
            
            # Verify that the code was saved correctly
            user.refresh_from_db()
            if not user.last_2fa_code or not user.last_2fa_time:
                logger.error(f"Failed to save 2FA code for user {user_id}")
                raise ValueError("Error al guardar el código 2FA")
            
            # Reset rate limit after successful code generation
            rate_limiter.reset_limit(user_id, 'two_factor')
            logger.info(f"2FA code generated for user {user_id}: {code}")
            
            return {"code": code}

        except ValueError as e:
            # Re-raise ValueError for rate limiting
            raise e
        except Exception as e:
            logger.error(f"Error generating 2FA code: {str(e)}", exc_info=True)
            raise ValueError(f"Error al generar código 2FA: {str(e)}")

    @staticmethod
    def verify_2fa_code(user, code):
        """Verifies if the 2FA code is valid"""
        # Verify that user is a CustomUser object
        if not isinstance(user, CustomUser):
            try:
                user = CustomUser.objects.get(id=user)
            except (ValueError, CustomUser.DoesNotExist):
                logger.error(f"User not found: {user}")
                return False
                
        try:
            # Rate limiting check for verification attempts
            user_id = user.id
            TwoFactorService._check_rate_limit(user_id)
            
            if not user.two_factor_secret:
                logger.warning(f"User {user_id} does not have 2FA enabled")
                return False
                
            if not code:
                logger.warning(f"No code provided for user {user_id}")
                return False
            
            # Log verification attempt
            logger.debug(f"Verifying 2FA for user {user_id}. Last code time: {user.last_2fa_time}")
            
            # Verify code is numeric and 6 digits
            if not (isinstance(code, str) and code.isdigit() and len(code) == 6):
                logger.warning(f"Invalid code format for user {user_id}: {code}")
                return False
                
            # Refresh user object to get latest code and time
            user.refresh_from_db()
            
            # Check if the code is expired
            time_diff = timezone.now() - user.last_2fa_time
            if time_diff.total_seconds() > 300:  # 5 minutes
                logger.warning(f"2FA code expired for user {user_id} (diff: {time_diff.total_seconds()}s)")
                return False
            
            # Compare the code directly
            result = user.last_2fa_code == code
            
            # Reset rate limit after successful verification
            if result:
                rate_limiter = RateLimitService()
                rate_limiter.reset_limit(user_id, 'two_factor')
                logger.info(f"2FA verification successful for user {user_id}")
            else:
                logger.warning(f"2FA verification failed for user {user_id}")
                
            return result

        except ValueError as e:
            # Rate limiting error
            logger.warning(f"Rate limit error for user {user.id}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error verifying 2FA code for user {user.id}: {str(e)}", exc_info=True)
            return False

    @staticmethod
    def send_2fa_code(user, code_data):
        """Sends the 2FA code via email"""
        try:
            # Check rate limiting before sending email
            user_id = user.id
            TwoFactorService._check_rate_limit(user_id, 'email_send')
            
            # Extract code from code_data, which could be dict or string
            if isinstance(code_data, dict):
                code = code_data.get('code')
            else:
                code = code_data
                
            if not code:
                logger.error(f"No code provided for sending to user {user_id}")
                raise ValueError("Código 2FA no proporcionado")
            
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
            user.two_factor_secret = secrets.token_hex(16) # 16 bytes

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
