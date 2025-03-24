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
            
            return {"token": token, "code": code}

        except ValueError as e:
            # Re-raise ValueError for rate limiting
            raise e
        except Exception as e:
            logger.error(f"Error generating 2FA code: {str(e)}", exc_info=True)
            raise ValueError(f"Error al generar código 2FA: {str(e)}")

    @staticmethod
    def verify_2fa_code(user, token_or_code):
        """Verifies if the 2FA code/token is valid"""
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
                
            if not token_or_code:
                logger.warning(f"No token/code provided for user {user_id}")
                return False
            
            # Log verification attempt
            logger.debug(f"Verifying 2FA for user {user_id}. Last code time: {user.last_2fa_time}")
            logger.debug(f"Input token/code type: {type(token_or_code)}")

            result = False
            
            # Attempt to decode JWT token
            try:
                logger.debug(f"Attempting JWT verification for user {user_id}")
                payload = jwt.decode(
                    token_or_code, 
                    settings.JWT_SECRET_KEY, 
                    algorithms=[settings.JWT_ALGORITHM]
                )
                
                # Verify token attributes
                if payload.get("type") != "2fa":
                    logger.warning(f"Invalid token type for user {user_id}: {payload.get('type')}")
                    return False
                    
                if payload.get("user_id") != user.id:
                    logger.warning(f"Token user_id mismatch for user {user_id}: {payload.get('user_id')} != {user.id}")
                    return False
                
                logger.info(f"JWT 2FA verification successful for user {user_id}")
                result = True
                
            except (jwt.InvalidTokenError, AttributeError, TypeError, ValueError) as e:
                # If JWT verification fails, try direct code comparison
                logger.info(f"JWT verification failed, trying direct code for user {user_id}: {str(e)}")
                
                # Refresh user object to get latest code and time
                user.refresh_from_db()
                
                # Check if user has last_2fa_code and last_2fa_time attributes
                if not hasattr(user, 'last_2fa_code') or user.last_2fa_code is None:
                    logger.error(f"User {user_id} missing last_2fa_code attribute or it's None")
                    return False
                
                if not hasattr(user, 'last_2fa_time') or user.last_2fa_time is None:
                    logger.error(f"User {user_id} missing last_2fa_time attribute or it's None")
                    return False
                
                # Check if the code is expired
                time_diff = timezone.now() - user.last_2fa_time
                if time_diff.total_seconds() > 300:  # 5 minutes
                    logger.warning(f"2FA code expired for user {user_id} (diff: {time_diff.total_seconds()}s)")
                    return False
                
                # Compare the code directly
                result = user.last_2fa_code == token_or_code
                logger.info(f"Direct code verification for user {user_id}: {result} (input: {token_or_code}, stored: {user.last_2fa_code})")
            
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
