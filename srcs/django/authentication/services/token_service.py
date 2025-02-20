from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.conf import settings
from datetime import datetime, timedelta
import jwt
import logging
from django.core.exceptions import ValidationError
from authentication.models import CustomUser
from .rate_limit_service import RateLimitService

logger = logging.getLogger(__name__)

"""
Token Service Module
-------------------
This service manages all token-related operations including:
- Token generation for different purposes (auth, email verification, password reset)
- Token verification and validation
- Token expiration management through Redis rate limiting

The service works in conjunction with RateLimitService to ensure:
- Proper token expiration times
- Rate limiting for token generation
- Protection against token abuse
"""

class TokenService:
    def __init__(self):
        self._rate_limiter = None

    @property
    def rate_limiter(self):
        if self._rate_limiter is None:
            self._rate_limiter = RateLimitService()
        return self._rate_limiter

    @staticmethod
    def generate_email_verification_token(user):
        """Generates a JWT token for email verification"""
        rate_limiter = RateLimitService()
        expiry_minutes = rate_limiter.get_token_expiry('email_verify')
        jwt_token = jwt.encode(
            {
                "user_id": user.id,
                "type": "email_verification",
                "exp": datetime.utcnow() + timedelta(minutes=expiry_minutes),
            },
            settings.JWT_SECRET_KEY,
            algorithm="HS256",
        )
        return {"uid": urlsafe_base64_encode(force_bytes(user.pk)), "token": jwt_token}

    @staticmethod
    def generate_password_reset_token(user):
        """Generates a JWT token for password reset"""
        rate_limiter = RateLimitService()
        expiry_minutes = rate_limiter.get_token_expiry('password_reset')
        jwt_token = jwt.encode(
            {
                "user_id": user.id,
                "type": "password_reset",
                "exp": datetime.utcnow() + timedelta(minutes=expiry_minutes),
            },
            settings.JWT_SECRET_KEY,
            algorithm="HS256",
        )

        return {"uid": urlsafe_base64_encode(force_bytes(user.pk)), "token": jwt_token}

    @staticmethod
    def generate_auth_token(user):
        """
        Generates a JWT token for authentication
        The payload is a dictionary containing:
        - user_id: User identifier
        - exp: Token expiration timestamp
        - iat: Token issue timestamp
        """
        rate_limiter = RateLimitService()
        expiry_minutes = rate_limiter.get_token_expiry('auth')
        payload = {  # payload is a diccionary with the data to encode in the token
            "user_id": user.id,
            "exp": datetime.utcnow() + timedelta(minutes=expiry_minutes),
            "iat": datetime.utcnow(),  # iat is the date when the token was emitted
        }
        token = jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,  # sign the token with the secret key specified in the configuration
            algorithm=settings.JWT_ALGORITHM,  # utilize the algorithm specified in the configuration
        )
        return token

    # Token verification
    @staticmethod
    def decode_jwt_token(token):
        """
        Decodes and validates a JWT token
        Raises ValidationError if token is expired or invalid
        """
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
        """
        Verifies a password reset token
        Returns the user if token is valid
        Raises ValidationError if token is invalid or expired
        """
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = CustomUser.objects.get(pk=uid)

            try:
                payload = jwt.decode(
                    token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
                )
            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
                logger.error(f"Token validation error: {str(e)}")
                raise ValidationError("Token inválido o expirado")

            if not (
                payload
                and payload.get("type") == "password_reset"
                and payload.get("user_id") == user.id
            ):
                logger.error("Token payload validation failed")
                raise ValidationError("Token inválido")

            return user

        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            raise ValidationError("Token inválido o expirado")
