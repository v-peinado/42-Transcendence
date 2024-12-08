from django.core.files.storage import default_storage
from django.core.exceptions import ValidationError
from PIL import Image
import io
import os

class ProfileImageService:
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_SIZE = 5 * 1024 * 1024  # 5MB
    
    @staticmethod
    def validate_image(image_file):
        """Validar formato y tamaño de imagen"""
        try:
            # Validar extensión
            ext = image_file.name.split('.')[-1].lower()
            if ext not in ProfileImageService.ALLOWED_EXTENSIONS:
                raise ValidationError(f"Formato no permitido. Use: {', '.join(ProfileImageService.ALLOWED_EXTENSIONS)}")
            
            # Validar tamaño
            if image_file.size > ProfileImageService.MAX_SIZE:
                raise ValidationError("La imagen no debe exceder 5MB")
            
            # Validar que sea una imagen válida
            try:
                img = Image.open(image_file)
                img.verify()
            except Exception:
                raise ValidationError("Archivo corrupto o inválido")
                
            return True
            
        except Exception as e:
            raise ValidationError(f"Error al validar imagen: {str(e)}")

    @staticmethod
    def delete_profile_image(user):
        """Eliminar imagen de perfil"""
        try:
            if user.profile_image:
                default_storage.delete(user.profile_image.path)
                user.profile_image = None
                user.save()
            return True
        except Exception as e:
            raise ValidationError(f"Error al eliminar imagen: {str(e)}")