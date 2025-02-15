from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.conf import settings
from datetime import datetime, timedelta
import jwt
from django.core.exceptions import ValidationError
from authentication.models import CustomUser

TOKEN_EXPIRATION = 15

# Generación de tokens 

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
    def generate_password_reset_token(user):
        """Genera un token JWT para reseteo de contraseña"""
        jwt_token = jwt.encode({
            'user_id': user.id,
            'type': 'password_reset',
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


# Verificación de tokens

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
            raise ValidationError("Token expirado")
        except jwt.InvalidTokenError:
            raise ValidationError("Token inválido")

    @staticmethod
    def verify_password_reset_token(uidb64, token):
        """Verifica un token de reseteo de contraseña"""
        try:
            # Decodificar UID y obtener usuario
            uid = urlsafe_base64_decode(uidb64).decode()
            user = CustomUser.objects.get(pk=uid)
            
            # Decodificar token directamente
            try:
                payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
                print("Error en decodificación JWT")
                raise ValidationError("Token inválido o expirado")
            
            print(f"Payload completo: {payload}")
            
            # Validaciones similares al cambio de email
            if not (payload and 
                   payload.get('type') == 'password_reset' and 
                   payload.get('user_id') == user.id):
                print("Validación de payload fallida")
                raise ValidationError("Token inválido")
                
            return user
            
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist) as e:
            print(f"DEBUG - Error en verificación: {str(e)}")
            raise ValidationError("Token inválido o expirado")