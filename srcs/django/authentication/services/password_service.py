from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import check_password
from ..models import PreviousPassword, CustomUser
from django.contrib import messages
from django.shortcuts import redirect
from authentication.models import CustomUser
import re
from django.utils.html import escape

class PasswordService:
    @staticmethod
    def validate_password_change(user, current_password, new_password1, new_password2):
        """Validar cambio de contraseña"""
        try:
            if not user.check_password(current_password):
                raise ValidationError('La contraseña actual es incorrecta')
                
            if new_password1 != new_password2:
                raise ValidationError('Las nuevas contraseñas no coinciden')
                
            # Validar que la contraseña no sea igual al username
            if new_password1.lower() == user.username.lower():
                raise ValidationError('La contraseña no puede ser igual al nombre de usuario')
                
            # Validar caracteres no permitidos
            if not all(char.isprintable() for char in new_password1):
                raise ValidationError('La contraseña no puede contener caracteres no imprimibles')
                
            try:
                validate_password(new_password1, user=user)
            except ValidationError as e:
                raise ValidationError(e.messages[0])
                
            # Validar contraseñas anteriores
            previous_passwords = PreviousPassword.objects.filter(user=user).order_by('-created_at')[:3]
            for prev_password in previous_passwords:
                if check_password(new_password1, prev_password.password):
                    raise ValidationError('No puedes reutilizar ninguna de tus últimas tres contraseñas')
                    
            return True
        except ValidationError as e:
            raise e

    @staticmethod
    def change_password(user, new_password):
        """Cambia la contraseña del usuario y guarda el historial"""
        try:
            user.set_password(new_password)
            user.save()
            PreviousPassword.objects.create(user=user, password=user.password)
            return True
        except Exception as e:
            raise ValidationError(f'Error al cambiar la contraseña: {str(e)}')

    @staticmethod
    def reset_password(user, new_password):
        """Restablece la contraseña del usuario (flujo de reset)"""
        try:
            user.set_password(new_password)
            user.save()
            PreviousPassword.objects.create(user=user, password=user.password)
            return True
        except Exception as e:
            raise ValidationError(f'Error al restablecer la contraseña: {str(e)}')

    @staticmethod
    def validate_manual_registration(username, email, password1, password2):
        """Validar datos de registro con protección contra XSS y SQL injection"""
        
        # Escapar HTML en username y email para evitar XSS
        username = escape(username)
        email = escape(email)
        
        # Lista de patrones peligrosos (XSS y SQL injection)
        dangerous_patterns = [
            '<script>',
            'javascript:',
            'onerror=',
            'onload=',
            'onclick=',
            'data:',
            'alert(',
            'eval(',
        ]
        
		# Validar que no contengan scripts maliciosos
        for pattern in dangerous_patterns:
            if pattern in username.lower() or pattern in email.lower():
                raise ValidationError(f"Caracteres no permitidos en '{username if pattern in username.lower() else email}'")
        
        # Validación de formato de email más estricta que la de Django
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValidationError(f"Formato de email '{email}' no válido")
        
        # Validar que no contengan scripts maliciosos
        if '<script>' in username.lower() or '<script>' in email.lower():
            raise ValidationError(f"Caracteres no permitidos en '{username if '<script>' in username.lower() else email}'")
        
        # Validar caracteres permitidos en el username
        if not all(char.isalnum() or char == '_' for char in username):
            raise ValidationError(f"El nombre de usuario '{username}' solo puede contener letras, números y guiones bajos")
            
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

        # Validar longitud mínima y máxima de la contraseña
        min_length_password = 8
        max_length_password = 20
        if len(password1) < min_length_password:
            raise ValidationError(f"La contraseña debe tener al menos {min_length_password} caracteres")
        if len(password1) > max_length_password:
            raise ValidationError(f"La contraseña no puede tener más de {max_length_password} caracteres")
        
        # Validar prefijo 42.
        if username.startswith('42.'):
            raise ValidationError("El prefijo '42.' está reservado para usuarios de 42")
            
        # Validar email de 42
        if re.match(r'.*@student\.42.*\.com$', email.lower()):
            raise ValidationError("Los correos con dominio @student.42*.com están reservados para usuarios de 42")
            
        # Validar contraseñas
        if password1 != password2:
            raise ValidationError("Las contraseñas no coinciden")
            
        # Validar que la contraseña no sea igual al username
        if password1.lower() == username.lower():
            raise ValidationError("La contraseña no puede ser igual al nombre de usuario")
            
        # Validar caracteres
        if not all(char.isprintable() for char in password1):
            raise ValidationError("La contraseña no puede contener caracteres no imprimibles")
            
        # Crear usuario temporal para validación
        temp_user = CustomUser(username=username)
        try:
            validate_password(password1, user=temp_user)
        except ValidationError as e:
            raise ValidationError(e.messages[0])
        
    @staticmethod
    def validate_printable_chars(text):
        """Valida que el texto solo contenga caracteres imprimibles y no espacios"""
        if not text:
            return False
        # Comprobar espacios y tabulaciones
        if any(char.isspace() for char in text):
            return False
        # Validar que todos los caracteres sean imprimibles
        return all(char.isprintable() and not char.isspace() for char in text)