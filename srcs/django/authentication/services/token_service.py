from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
import jwt
from datetime import datetime, timedelta

class TokenService:
    @staticmethod
    def generate_verification_token(user):
        """Genera un token JWT para verificación de email"""
        jwt_token = jwt.encode({
            'user_id': user.id,
            'type': 'email_verification',
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, settings.JWT_SECRET_KEY, algorithm='HS256')

        return {
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': jwt_token
        }

    @staticmethod
    def generate_password_reset_token(user):
        """Genera un token JWT para reseteo de contraseña"""
        return jwt.encode({
            'user_id': user.id,
            'type': 'password_reset',
            'exp': datetime.utcnow() + timedelta(hours=1)
        }, settings.JWT_SECRET_KEY, algorithm='HS256')

    @staticmethod
    def get_uid_for_user(user):
        """Genera un UID seguro para el usuario"""
        return urlsafe_base64_encode(force_bytes(user.pk))

def decode_jwt_token(token):
    """Decodifica un token JWT"""
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=['HS256']
        )
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None