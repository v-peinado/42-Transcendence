from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.conf import settings
from datetime import datetime, timedelta
import jwt
from django.core.exceptions import ValidationError
from authentication.models import CustomUser

TOKEN_EXPIRATION = 15


# Token generation service
class TokenService:
    @staticmethod
    def generate_email_verification_token(user):
        """Generates a JWT token for email verification"""
        jwt_token = jwt.encode(
            {
                "user_id": user.id,
                "type": "email_verification",
                "exp": datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRATION),
            },
            settings.JWT_SECRET_KEY,
            algorithm="HS256",
        )

        return {"uid": urlsafe_base64_encode(force_bytes(user.pk)), "token": jwt_token}

    @staticmethod
    def generate_password_reset_token(user):
        """Generates a JWT token for password reset"""
        jwt_token = jwt.encode(
            {
                "user_id": user.id,
                "type": "password_reset",
                "exp": datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRATION),
            },
            settings.JWT_SECRET_KEY,
            algorithm="HS256",
        )

        return {"uid": urlsafe_base64_encode(force_bytes(user.pk)), "token": jwt_token}

    @staticmethod
    def generate_auth_token(user):
        """Generates a JWT token for authentication"""
        payload = {  # payload is a diccionary with the data to encode in the token
            "user_id": user.id,
            "exp": datetime.utcnow()
            + timedelta(
                minutes=TOKEN_EXPIRATION
            ),  # exp is the expiration date of the token (15 minutes after the current date)
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
        """Decodes a JWT token"""
        try:
            return jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
        except jwt.ExpiredSignatureError:
            raise ValidationError("Token expirado")
        except jwt.InvalidTokenError:
            raise ValidationError("Token inválido")

    @staticmethod
    def verify_password_reset_token(uidb64, token):
        """Verifies a password reset token"""
        try:
            # Decode user ID from base64
            uid = urlsafe_base64_decode(uidb64).decode()
            user = CustomUser.objects.get(pk=uid)

            # Decode token and verify payload
            try:
                payload = jwt.decode(
                    token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
                )
            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
                print("Error en decodificación JWT")
                raise ValidationError("Token inválido o expirado")

            print(f"Payload completo: {payload}")

            # Email verification token validation
            if not (
                payload
                and payload.get("type") == "password_reset"
                and payload.get("user_id") == user.id
            ):
                print("Validación de payload fallida")
                raise ValidationError("Token inválido")

            return user

        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist) as e:
            print(f"DEBUG - Error en verificación: {str(e)}")
            raise ValidationError("Token inválido o expirado")
