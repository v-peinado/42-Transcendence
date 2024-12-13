from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from datetime import datetime, timedelta
import jwt

TOKEN_EXPIRATION = 15

class TokenService:
    @staticmethod
    def generate_email_verification_token(user):
        """Genera un token JWT para verificación de email"""
        jwt_token = jwt.encode({
            'user_id': user.id,
            'type': 'email_verification',
            'exp': datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRATION),
        }, settings.JWT_SECRET_KEY, algorithm='HS256')

        return {
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': jwt_token
        }

    @staticmethod
    def generate_auth_token(user):
        """Genera un token JWT para autenticación"""
        payload = {  															# payload es un diccionario con la información que se quiere codificar en el token
            'user_id': user.id,  												# user_id es el id del usuario
            'exp': datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRATION),  	# exp es la fecha de expiración del token (15 minutos por defecto)
            'iat': datetime.utcnow() 											# iat es la fecha de emisión del token
        }
        token = jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,  											# firmar el token con la clave secreta de la aplicación
            algorithm=settings.JWT_ALGORITHM  									# usar el algoritmo de codificación especificado en la configuración
        )
        return token

    @staticmethod
    def decode_jwt_token(token):
        """Decodifica un token JWT"""
        try:
            return jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None