from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.conf import settings
from ..models import CustomUser
import re

class ProfileService:
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

            # Manejar imagen de perfil
            if files and 'profile_image' in files:
                image = files['profile_image']
                
                # Validar tamaño
                if image.size > 5 * 1024 * 1024:  # 5MB
                    raise ValidationError("La imagen no debe exceder 5MB")
                
                # Validar extensión
                valid_extensions = ['jpg', 'jpeg', 'png', 'gif']
                ext = image.name.split('.')[-1].lower()
                if ext not in valid_extensions:
                    raise ValidationError(f"Formato no permitido. Use: {', '.join(valid_extensions)}")
                
                # Eliminar imagen anterior si existe
                if user.profile_image:
                    default_storage.delete(user.profile_image.path)
                
                # Guardar nueva imagen
                user.profile_image = image

            user.save()
            return True
            
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
    def get_profile_data(user):
        """Obtener datos del perfil"""
        return {
            'username': user.username,
            'email': user.email,
            'profile_image': user.profile_image.url if user.profile_image else None,
            'is_fortytwo_user': user.is_fortytwo_user,
            'fortytwo_image': user.fortytwo_image if user.is_fortytwo_user else None,
            'date_joined': user.date_joined,
            'email_verified': user.email_verified,
            'two_factor_enabled': user.two_factor_enabled
        }