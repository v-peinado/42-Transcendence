from django.utils.http import urlsafe_base64_decode
from django.core.exceptions import ValidationError
from authentication.models import CustomUser
from .mail_service import MailSendingService
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