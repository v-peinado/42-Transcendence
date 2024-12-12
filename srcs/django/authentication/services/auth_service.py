from django.utils.http import urlsafe_base64_decode
from django.core.exceptions import ValidationError
from authentication.models import CustomUser
from .verify_email_service import EmailService
from .token_service import TokenService
import jwt

class AuthenticationService:
    @staticmethod
    def register_user(username, email, password):
        """Verificar que el usuario no exista y crearlo"""
        # Validar que el usuario no exista
        if CustomUser.objects.filter(username=username).exists():
            raise ValidationError("Este nombre de usuario ya está en uso")
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("Este email ya está en uso")
            
        user = CustomUser.objects.create_user(
            username=username.lower(),
            email=email.lower(),
            password=password,
            is_active=False
        )
        return user

    @staticmethod
    def verify_email(uidb64, token):
        """Verificar email del usuario"""
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = CustomUser.objects.get(pk=uid)
            payload = TokenService.decode_jwt_token(token)
            
            if user and payload and payload['user_id'] == user.id:
                user.email_verified = True
                user.is_active = True
                user.email_verification_token = None
                user.save()
                
                # Enviar email de bienvenida
                EmailService.send_welcome_email(user)
                return True
            else:
                raise ValidationError("Token de verificación inválido")
                
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist, jwt.InvalidTokenError):
            raise ValidationError("El enlace de verificación no es válido")
        except Exception as e:
            raise ValidationError(f"Error al verificar email: {str(e)}")