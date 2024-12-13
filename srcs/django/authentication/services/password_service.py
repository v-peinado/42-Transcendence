from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import check_password
from ..models import PreviousPassword, CustomUser
from .token_service import TokenService
from .mail_service import MailSendingService
from authentication.models import CustomUser
from django.utils.html import escape
import re

class PasswordService:
    @staticmethod
    def _validate_password_basic(user, new_password1, new_password2):
        """Validaciones básicas de contraseña"""
        if new_password1 != new_password2:
            raise ValidationError("Las contraseñas no coinciden")
            
        if new_password1.lower() == user.username.lower():
            raise ValidationError("La contraseña no puede ser igual al nombre de usuario")
            
        if not all(char.isprintable() for char in new_password1):
            raise ValidationError("La contraseña no puede contener caracteres no imprimibles")

        # Longitudes
        min_length = 8
        max_length = 20
        if len(new_password1) < min_length:
            raise ValidationError(f"La contraseña debe tener al menos {min_length} caracteres")
        if len(new_password1) > max_length:
            raise ValidationError(f"La contraseña no puede tener más de {max_length} caracteres")

        # Validaciones estándar de Django
        validate_password(new_password1, user)
        
        # Histórico
        previous_passwords = PreviousPassword.objects.filter(user=user).order_by('-created_at')[:3]
        for prev_password in previous_passwords:
            if check_password(new_password1, prev_password.password):
                raise ValidationError('No puedes reutilizar ninguna de tus últimas tres contraseñas')

    @staticmethod
    def validate_password_change(user, current_password, new_password1, new_password2):
        """Validar cambio de contraseña"""
        if not user.check_password(current_password):
            raise ValidationError('La contraseña actual es incorrecta')
            
        PasswordService._validate_password_basic(user, new_password1, new_password2)
        return True

    @staticmethod
    def validate_manual_registration(username, email, password1, password2):
        """Validar datos de registro con protección contra XSS y SQL injection"""
        
        # Escapar HTML en username y email para evitar XSS
        username = escape(username)
        email = escape(email)
        
        # Lista de patrones peligrosos (XSS , SQL injection, Path Traversal, Command Injection, Control Characters)
        dangerous_patterns = [
            '<script>', 'javascript:', 'onerror=', 'onload=', 'onclick=', 'data:', 'alert(', 'eval(',	#XSS
            'SELECT', 'UNION', '--',                          											# SQL Injection
    		'../', '..\\',                                     											# Path Traversal
    		'&', '|', ';', '`', '$', '(', ')', '{', '}',     											# Command Injection
   			 '\0', '\n', '\r', '\t', '\b'                      											# Control Characters
        ]
        
		# Validar que no contengan scripts maliciosos
        for pattern in dangerous_patterns:
            if pattern in username.lower() or pattern in email.lower():
                raise ValidationError(f"Caracteres no permitidos detectados en '{username if pattern in username.lower() else email}'")
        
        # Verificar caracteres permitidos
        if not all(char.isalnum() or char in allowed_chars for char in username):
            raise ValidationError("Solo se permiten letras, números y los caracteres: - . _ @ +")
            
		# Validación de formato de email más estricta que la de Django
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValidationError(f"Formato de email '{email}' no válido")
        
        # Verificar si ya existe el usuario
        if CustomUser.objects.filter(username=username.lower()).exists():
            raise ValidationError(f"El nombre de usuario '{username}' ya está en uso")
        
        # Verificar si ya existe el email
        if CustomUser.objects.filter(email=email.lower()).exists():
            raise ValidationError(f"El email '{email}' ya está registrado")
        
        # Validar longitud del username
        max_length_username = 10
        if len(username) > max_length_username:
            raise ValidationError(f"El nombre de usuario no puede tener más de {max_length_username} caracteres")

        # Validar prefijo 42.
        if username.startswith('42.'):
            raise ValidationError("El prefijo '42.' está reservado para usuarios de 42")
            
        # Validar email de 42
        if re.match(r'.*@student\.42.*\.com$', email.lower()):
            raise ValidationError("Los correos con dominio @student.42*.com están reservados para usuarios de 42")
            
        # Validar contraseñas
        PasswordService._validate_password_basic(CustomUser(username=username), password1, password2)

    @staticmethod
    def initiate_password_reset(email):
        """Iniciar proceso de reset de contraseña"""
        if re.match(r'.*@student\.42.*\.com$', email.lower()):
            raise ValidationError("Los usuarios de 42 deben iniciar sesión a través del botón de login de 42")

        users = CustomUser.objects.filter(
            email__iexact=email,
            is_active=True,
            is_fortytwo_user=False
        )

        if not users.exists():
            # fallar silenciosamente para no revelar existencia de usuarios
            return False

        user = users.first()
        if user.is_fortytwo_user:
            raise ValidationError("Los usuarios de 42 no pueden usar esta función")

        token = TokenService.generate_password_reset_token(user)
        MailSendingService.send_password_reset_email(user, token)
        return True

    @staticmethod
    def confirm_password_reset(uidb64, token, new_password1, new_password2):
        """Confirmar reset de contraseña"""
        try:
            user = TokenService.verify_password_reset_token(uidb64, token)
            
            PasswordService._validate_password_basic(user, new_password1, new_password2)
            
            user.set_password(new_password1)
            user.save()
            PreviousPassword.objects.create(user=user, password=user.password)
            MailSendingService.send_password_changed_notification(user, is_reset=True)
            return True
        except Exception as e:
            raise ValidationError(str(e))