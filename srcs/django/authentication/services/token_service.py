from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from datetime import datetime, timedelta, timezone
from django.core.exceptions import ValidationError
from .rate_limit_service import RateLimitService
from django.utils.encoding import force_bytes
from authentication.models import CustomUser
from django.conf import settings
import logging
import jwt

# JWT Token Service
# This service handles all aspects of JWT (JSON Web Token) management in the application:

#  Generation:
#    - Creates signed tokens for email verification, password reset, and OAuth authentication
#    - Each token contains user_id, token type and expiration
#    - Tokens use strong cryptographic signing with HS256 algorithm
#    - All tokens have properly limited expiration times (rate limit service)
#    - All tokens include expiration timestamps
#    - UTC timezone used for all time-based operations

#  Structure:
#    - Header: Contains algorithm (HS256) and token type (JWT)
#    - Payload: Contains user ID, token type, expiration, and issue time
#    - Signature: Cryptographically secures the token using JWT_SECRET_KEY

#  The service works in conjunction with RateLimitService to ensure:
#	 - Proper token expiration times
#	 - Rate limiting for token generation
#	 - Protection against token abuse

logger = logging.getLogger(__name__)

class TokenService:
    def __init__(self):
        self._rate_limiter = None
        # Validate critical JWT settings on initialization
        if not hasattr(settings, 'JWT_SECRET_KEY') or not settings.JWT_SECRET_KEY:
            logger.critical("JWT_SECRET_KEY not configured - this is a critical security issue")
            raise RuntimeError("JWT_SECRET_KEY must be set for token operations")
        
        if not hasattr(settings, 'JWT_ALGORITHM') or not settings.JWT_ALGORITHM:
            logger.warning("JWT_ALGORITHM not configured, using default 'HS256'")

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
        """
        The token contains:
        - user_id: The ID of the user to verify (used for authentication)
        - type: "email_verification" (indicates the token's purpose)
        - exp: Expiration timestamp (UTC)
        
        The token is signed with JWT_SECRET_KEY using the HS256 algorithm.
        The returned UID is the user's ID encoded in URL-safe base64.
        
        Example token structure:
        Header:  {"alg": "HS256", "typ": "JWT"}
        Payload: {"user_id": 1, "type": "email_verification", "exp": 1742901505}
        """
        service = cls()
        # Verify rate limit for email_verification
        is_limited, remaining_time = service.rate_limiter.is_rate_limited(
            user.id, 'email_verification')
        
        if is_limited:
            logger.warning(f"Rate limit exceeded for user {user.id} on email verification")
            raise ValidationError(f"Please wait {remaining_time} seconds before requesting another verification email")
        
        # Validate JWT_SECRET_KEY explicitly
        if not settings.JWT_SECRET_KEY:
            logger.critical("Cannot generate token: JWT_SECRET_KEY not set")
            raise ValidationError("Server error: JWT_SECRET_KEY not set")
            
        expiry_minutes = service.rate_limiter.get_token_expiry('email_verify')
        jwt_token = jwt.encode( # encode following dictionary...
            {
                "user_id": user.id,
                "type": "email_verification",
                "exp": datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes),
            },
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        logger.info(f"Email verification token generated for user {user.id}")
        return {"uid": urlsafe_base64_encode(force_bytes(user.pk)), "token": jwt_token}

    @classmethod
    def generate_password_reset_token(cls, user):
        """
        The token contains:
        - user_id: The ID of the user requesting the reset (used for authentication)
        - type: "password_reset" (indicates the token's purpose)
        - exp: Expiration timestamp (UTC)
        
        The token is signed with JWT_SECRET_KEY using the HS256 algorithm.
        The returned UID is the user's ID encoded in URL-safe base64.
        
        Example token structure:
        Header:  {"alg": "HS256", "typ": "JWT"}
        Payload: {"user_id": 1, "type": "password_reset", "exp": 1742901505}
        """
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
                "exp": datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes),
            },
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        logger.info(f"Password reset token generated for user {user.id}")
        return {"uid": urlsafe_base64_encode(force_bytes(user.pk)), "token": jwt_token}

    @classmethod
    def generate_auth_token(cls, user):
        """
        The token contains:
        - user_id: The ID of the authenticated user
        - exp: Expiration timestamp (UTC)
        - iat: Issued At timestamp (UTC) - when the token was created
        
        This token doesn't include a 'type' field since it's only used for authentication.
        The token is signed with JWT_SECRET_KEY using the HS256 algorithm.
        
        Example token structure:
        Header:  {"alg": "HS256", "typ": "JWT"}
        Payload: {"user_id": 1, "exp": 1742901505, "iat": 1742900605}
        """
        service = cls()
        expiry_minutes = service.rate_limiter.get_token_expiry('auth')
        payload = {  # payload is a diccionary with the data to encode in the token
            "user_id": user.id,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes),
            "iat": datetime.now(timezone.utc),  # iat is the date when the token was emitted
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
        """
         - Verifies the signature using JWT_SECRET_KEY
         - Checks that the token hasn't expired
         - Returns the decoded payload if valid
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
         - Decodes the base64 user ID
         - Retrieves the user from the database
         - Decodes and validates the JWT token
         - Verifies the token type is "password_reset"
         - Ensures the user ID in the token matches the decoded user ID
        """
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
