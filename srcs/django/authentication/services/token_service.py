from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.exceptions import ValidationError
from .rate_limit_service import RateLimitService
from django.utils.encoding import force_bytes
from authentication.models import CustomUser
from datetime import datetime, timedelta
from django.conf import settings
import logging
import jwt

# This service manages all token-related operations including:
#	- Token generation for different purposes (auth, email verification, password reset)
#	- Token verification and validation
#	- Token expiration management through Redis rate limiting

# The service works in conjunction with RateLimitService to ensure:
#	- Proper token expiration times
#	- Rate limiting for token generation
#	- Protection against token abuse

logger = logging.getLogger(__name__)

class TokenService:
    def __init__(self):
        self._rate_limiter = None

# @property decorator transforms a method into a virtual attribute, allowing you to access it
# as if it were a regular attribute (without parentheses) while still executing code.
# This approach allows us to defer the cost of creating the RateLimitService until it's actually
# required, following the principle of "pay only for what you use".
# We use here because this method utilizes redis, which is an expensive operation.

    @property
    def rate_limiter(self):
        """To access rate limit service before using it for token generation"""
        if self._rate_limiter is None:
            self._rate_limiter = RateLimitService()
        return self._rate_limiter

#### Token generation methods ####

    @classmethod
    def generate_email_verification_token(cls, user):
        """Generates a JWT token for email verification"""
        service = cls()
        # Verify rate limit for email_verification
        is_limited, remaining_time = service.rate_limiter.is_rate_limited(
            user.id, 'email_verification')
        
        if is_limited:
            logger.warning(f"Rate limit exceeded for user {user.id} on email verification")
            raise ValidationError(f"Please wait {remaining_time} seconds before requesting another verification email")
        
        expiry_minutes = service.rate_limiter.get_token_expiry('email_verify')
        jwt_token = jwt.encode( # encode following dictionary...
            {
                "user_id": user.id,
                "type": "email_verification",
                "exp": datetime.utcnow() + timedelta(minutes=expiry_minutes),
            },
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        logger.info(f"Email verification token generated for user {user.id}")
        return {"uid": urlsafe_base64_encode(force_bytes(user.pk)), "token": jwt_token}

    @classmethod
    def generate_password_reset_token(cls, user):
        """Generates a JWT token for password reset"""
        service = cls()
        # Verify rate limit for password_reset
        is_limited, remaining_time = service.rate_limiter.is_rate_limited(
            user.id, 'password_reset')
        
        if is_limited:
            logger.warning(f"Rate limit exceeded for user {user.id} on password reset")
            raise ValidationError(f"Please wait {remaining_time} seconds before requesting another password reset")
            
        expiry_minutes = service.rate_limiter.get_token_expiry('password_reset')
        jwt_token = jwt.encode(
            {
                "user_id": user.id,
                "type": "password_reset",
                "exp": datetime.utcnow() + timedelta(minutes=expiry_minutes),
            },
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        logger.info(f"Password reset token generated for user {user.id}")
        return {"uid": urlsafe_base64_encode(force_bytes(user.pk)), "token": jwt_token}

    @classmethod
    def generate_auth_token(cls, user):
        """ Generates a JWT token for oauth authentication (fortytwo service) """
        service = cls()
        expiry_minutes = service.rate_limiter.get_token_expiry('auth')
        payload = {  # payload is a diccionary with the data to encode in the token
            "user_id": user.id,
            "exp": datetime.utcnow() + timedelta(minutes=expiry_minutes),
            "iat": datetime.utcnow(),  # iat is the date when the token was emitted
        }
        token = jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        return token

#### Token verification methods ####

    @staticmethod
    def decode_jwt_token(token):
        """ Decodes and validates a JWT token """
        try:
            return jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired attempt")
            raise ValidationError("Token expirado")
        except jwt.InvalidTokenError:
            logger.warning("Invalid token attempt")
            raise ValidationError("Token inválido")

    @staticmethod
    def verify_password_reset_token(uidb64, token):
        """ Verifies a password reset token (returns user if valid) """
        try:
            uid = urlsafe_base64_decode(uidb64).decode() # Decode uid from base64
            user = CustomUser.objects.get(pk=uid) # Get user from database

            try: # Decode and validate token
                payload = jwt.decode(
                    token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
                )
            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
                logger.error(f"Token validation error: {str(e)}")
                raise ValidationError("Token inválido o expirado")

            if not ( # "if not all conditions are met, raise an error..."
                payload
                and payload.get("type") == "password_reset"
                and payload.get("user_id") == user.id
            ):
                logger.error("Token payload validation failed")
                raise ValidationError("Token inválido")

            return user # if all OK, return user

        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            raise ValidationError("Token inválido o expirado")
