from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from ..models import CustomUser
from .token_service import TokenService
from .mail_service import MailSendingService
from .password_service import PasswordService
from ..models import PreviousPassword
from .gdpr_service import GDPRService
import re
import base64


class ProfileService:
    @staticmethod
    def handle_image_restoration(user):
        """Maneja restauración de imágenes de perfil"""
        if user.is_fortytwo_user:
            ProfileService.restore_default_image(user)
            return 'Imagen de perfil restaurada a la imagen de 42'
        else:
            ProfileService.restore_default_image(user)
            return 'Imagen de perfil restaurada a la imagen por defecto'

    @staticmethod
    def handle_email_change(user, new_email):
        """Maneja cambio de email para usuarios manuales"""
        if re.match(r'.*@student\.42.*\.com$', new_email.lower()):
            raise ValidationError('Los correos con dominio @student.42*.com están reservados para usuarios de 42')
            
        if CustomUser.objects.exclude(id=user.id).filter(email=new_email).exists():
            raise ValidationError('Este email ya está en uso')

        token_data = TokenService.generate_email_verification_token(user)
        user.pending_email = new_email
        user.pending_email_token = token_data['token']
        user.save()

        verification_data = {
            'uid': token_data['uid'],
            'token': token_data['token'],
            'new_email': new_email,
            'verification_url': f"{settings.SITE_URL}/verify-email-change/{token_data['uid']}/{token_data['token']}/"
        }

        MailSendingService.send_email_change_verification(user, verification_data)
        return 'Te hemos enviado un email para confirmar el cambio'

    @staticmethod
    def handle_password_change(user, current_password, new_password1, new_password2):
        """Maneja cambio de contraseña"""
        PasswordService.validate_password_change(user, current_password, new_password1, new_password2)
        user.set_password(new_password1)
        user.save()
        
        PreviousPassword.objects.create(user=user, password=user.password)
        return True

    @staticmethod
    def update_profile(user, data, files=None):
        """Actualizar perfil del usuario"""
        try:
            # Validar y actualizar email si no es usuario de 42
            if not user.is_fortytwo_user and 'email' in data:
                email = data.get('email')
                if email != user.email:
                    # Validar que no sea email de 42
                    if re.match(r'.*@student\.42.*\.com$', email.lower()):
                        raise ValidationError("Los correos con dominio @student.42*.com están reservados para usuarios de 42")
                    
                    # Validar que el email no esté en uso
                    if CustomUser.objects.exclude(id=user.id).filter(email=email).exists():
                        raise ValidationError("Este email ya está en uso")
                    
                    user.email = email.lower()

            # Procesar imagen - sea base64 o archivo
            profile_image = None
            
            # Revisar si viene una imagen en base64
            if data.get('profile_image_base64'):
                try:
                    format, imgstr = data['profile_image_base64'].split(';base64,')
                    ext = format.split('/')[-1]
                    profile_image = ContentFile(
                        base64.b64decode(imgstr), 
                        name=f'profile_{user.id}.{ext}'
                    )
                except Exception as e:
                    raise ValidationError(f"Error procesando imagen base64: {str(e)}")

            # Si no hay base64, revisar si hay archivo
            elif files and 'profile_image' in files:
                profile_image = files['profile_image']

            # Si hay imagen (de cualquier fuente), procesarla
            if profile_image:
                # Validar tamaño
                if profile_image.size > 5 * 1024 * 1024:  # 5MB
                    raise ValidationError("La imagen no debe exceder 5MB")
                
                # Validar extensión
                valid_extensions = ['jpg', 'jpeg', 'png', 'gif']
                ext = profile_image.name.split('.')[-1].lower()
                if ext not in valid_extensions:
                    raise ValidationError(f"Formato no permitido. Use: {', '.join(valid_extensions)}")
                
                # Eliminar imagen anterior si existe
                if user.profile_image:
                    default_storage.delete(user.profile_image.path)
                
                # Guardar nueva imagen
                user.profile_image = profile_image

            user.save()
            return {
                'email': user.email,
                'profile_image_url': user.profile_image.url if user.profile_image else None
            }
            
        except Exception as e:
            raise ValidationError(f"Error al actualizar perfil: {str(e)}")

    @staticmethod
    def restore_default_image(user):
        """Restaurar imagen de perfil por defecto"""
        try:
            # Si hay una imagen personalizada, eliminarla
            if user.profile_image:
                default_storage.delete(user.profile_image.path)
            
            # Restablecer la imagen por defecto
            user.profile_image = None
            
            # Para usuarios de 42, asegurarse de que se use la imagen de la intra
            if user.is_fortytwo_user:
                user.fortytwo_image = user.fortytwo_image_url
            
            user.save()
            return True
            
        except Exception as e:
            raise ValidationError(f"Error al restaurar imagen: {str(e)}")

    @staticmethod
    def get_user_profile_data(user):
        """Obtener datos del perfil de usuario"""
        if not user.is_authenticated:
            raise ValidationError('Usuario no autenticado')
            
        data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_active': user.is_active,
            'email_verified': user.email_verified,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'is_fortytwo_user': user.is_fortytwo_user,
            'fortytwo_image': user.fortytwo_image  # Asegurémonos de que este campo existe
        }
        print("DEBUG - Profile data:", data)  # Para ver qué datos nos llegan
        return data

    @staticmethod
    def delete_user_account(user, password=None):
        """Gestiona eliminación de cuenta"""
        # Validar contraseña para usuarios no-42
        if not user.is_fortytwo_user:
            if not password or not user.check_password(password):
                raise ValidationError('Contraseña incorrecta')
        
        # Delegar eliminación a GDPRService
        GDPRService.delete_user_data(user)
        return True