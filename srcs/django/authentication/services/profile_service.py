from django.core.files.storage import default_storage
from django.core.exceptions import ValidationError
from .rate_limit_service import RateLimitService
from django.core.files.base import ContentFile
from .password_service import PasswordService
from authentication.models import UserSession
from .mail_service import MailSendingService
from .token_service import TokenService
from ..models import PreviousPassword
from .gdpr_service import GDPRService
from django.conf import settings
from ..models import CustomUser
from pathlib import Path
import logging
import base64
import time
import re
import os

logger = logging.getLogger(__name__)

class ProfileService:
    def __init__(self):
        self.rate_limiter = RateLimitService()

    @staticmethod
    def handle_image_restoration(user):
        """Handles profile image restoration"""
        if user.is_fortytwo_user:
            ProfileService.restore_default_image(user)
            return "Imagen de perfil restaurada a la imagen de 42"
        else:
            ProfileService.restore_default_image(user)
            return "Imagen de perfil restaurada a la imagen por defecto"

    @staticmethod
    def handle_email_change(user, new_email):
        """Handles email change for manual users"""
        rate_limiter = RateLimitService()
        is_limited, remaining_time = rate_limiter.is_rate_limited(user.id, 'email_change')
        
        if is_limited:
            logger.warning(f"Rate limit exceeded for user {user.id} on email change")
            raise ValidationError(f"Please wait {remaining_time} seconds before requesting another email change")

        if re.match(r".*@student\.42.*\.com$", new_email.lower()):
            raise ValidationError(
                "Los correos con dominio @student.42*.com están reservados para usuarios de 42")

        if CustomUser.objects.exclude(id=user.id).filter(email=new_email).exists():
            raise ValidationError("Este email ya está en uso")

        token_data = TokenService.generate_email_verification_token(user)
        user.pending_email = new_email
        user.pending_email_token = token_data["token"]
        user.save()

        verification_data = {
            "uid": token_data["uid"], # id user
            "token": token_data["token"], # jwt_token (for email verification)
            "new_email": new_email,
            # send verification URL to user's email (id + jwt_token)
            "verification_url": f"{settings.SITE_URL}/verify-email-change/{token_data['uid']}/{token_data['token']}/"}

        MailSendingService.send_email_change_verification(user, verification_data)
        rate_limiter.reset_limit(user.id, 'email_change') # reset rate limit on successfull email change
        return "Te hemos enviado un email para confirmar el cambio"

    @staticmethod
    def handle_password_change(user, current_password, new_password1, new_password2):
        """Handles password change"""
        PasswordService.validate_password_change( # first check if the old password is correct
            user, current_password, new_password1, new_password2 )
        
        # set_password hashes the password and saves it in the database 
		# (see: https://docs.djangoproject.com/en/3.2/topics/auth/default/#changing-passwords)
        user.set_password(new_password1)
        user.save()

        PreviousPassword.objects.create(user=user, password=user.password)
        return True

    @staticmethod
    def update_profile(user, data, files=None):
        """Updates user profile"""
        rate_limiter = RateLimitService()
        is_limited, remaining_time = rate_limiter.is_rate_limited(user.id, 'profile_update')
        
        if is_limited: # if the user is rate limited, raise an error
            logger.warning(f"Rate limit exceeded for user {user.id} on profile update")
            raise ValidationError(f"Please wait {remaining_time} seconds before updating your profile again")

        try:
            if not user.is_fortytwo_user and "email" in data: 
                # if the user is not a 42 user and the email is in the data
                # (42 users cannot change their email)
                email = data.get("email")
                if email != user.email:
                    if re.match(r".*@student\.42.*\.com$", email.lower()):
                        raise ValidationError(
                            "Los correos con dominio @student.42*.com están reservados para usuarios de 42")

                    if (
                        CustomUser.objects.exclude(id=user.id)
                        .filter(email=email)
                        .exists()
                    ):
                        raise ValidationError("Este email ya está en uso")

                    user.email = email.lower()

            profile_image = None

            if data.get("profile_image_base64"):
                # We receive the image as base64 encoded string because it's sent from the frontend
                # We need to decode it and save it as a file
                try:
                    format, imgstr = data["profile_image_base64"].split(";base64,")
                    ext = format.split("/")[-1]
                    profile_image = ContentFile(
                        base64.b64decode(imgstr), name=f"profile_{user.id}.{ext}"
                    )
                except Exception as e:
                    raise ValidationError(f"Error procesando imagen base64: {str(e)}")

            elif files and "profile_image" in files: # if the profile_image is in the files (from the frontend)
                profile_image = files["profile_image"]

            if profile_image:
                if profile_image.size > 2 * 1024 * 1024:
                    error_msg = f"User {user.id} attempted to upload oversized image: {profile_image.size / (1024*1024):.2f}MB (max: 2MB)"
                    logger.warning(error_msg)
                    raise ValidationError("La imagen no debe exceder 2MB")

                valid_extensions = ["jpg", "jpeg", "png", "gif"]
                ext = profile_image.name.split(".")[-1].lower()
                if ext not in valid_extensions:
                    raise ValidationError(
                        f"Formato no permitido. Use: {', '.join(valid_extensions)}"
                    )

                # Ensure profile_images directory exists and has correct permissions
                media_root = Path(settings.MEDIA_ROOT)
                profile_images_dir = media_root / 'profile_images'
                profile_images_dir.mkdir(parents=True, exist_ok=True)
                os.chmod(profile_images_dir, 0o755)

                # Generate unique filename
                timestamp = int(time.time())
                filename = f"profile_{user.id}_{timestamp}.{ext}"
                relative_path = f'profile_images/{filename}'
                file_path = media_root / relative_path

                # Erase old image if it exists
                if user.profile_image:
                    try:
                        old_path = Path(user.profile_image.path)
                        if old_path.exists():
                            os.remove(old_path)
                    except Exception as e:
                        logger.warning(f"Error removing old image: {e}")

                # Save new image
                try:
                    with open(file_path, 'wb+') as destination:
                        for chunk in profile_image.chunks():
                            destination.write(chunk)
                    os.chmod(file_path, 0o644)
                    user.profile_image = relative_path
                except Exception as e:
                    logger.error(f"Error saving image: {e}")
                    raise ValidationError(f"Error al guardar la imagen: {str(e)}")

            user.save()
            rate_limiter.reset_limit(user.id, 'profile_update') # reset rate limit on successful profile update
            
            # Build profile image URL
            profile_image_url = None
            if user.profile_image:
                profile_image_url = f"{settings.MEDIA_URL}{user.profile_image}"

            return {
                "email": user.email,
                "profile_image_url": profile_image_url
            }

        except Exception as e:
            logger.error(f"Error updating profile: {str(e)}")
            raise ValidationError(f"Error al actualizar perfil: {str(e)}")

    @staticmethod
    def restore_default_image(user):
        """Restores default profile image"""
        try:
            if user.profile_image:
                default_storage.delete(user.profile_image.path)

            user.profile_image = None

            if user.is_fortytwo_user:
                user.fortytwo_image = user.fortytwo_image_url

            user.save()
            return True

        except Exception as e:
            raise ValidationError(f"Error al restaurar imagen: {str(e)}")

    @staticmethod
    def get_user_profile_data(user):
        """Gets user profile data to display in the profile view"""
        if not user.is_authenticated:
            raise ValidationError("Usuario no autenticado")

        profile_image_url = None # default profile image URL
        if user.profile_image:
            profile_image_url = f"{settings.SITE_URL}{settings.MEDIA_URL}{user.profile_image}"

        data = {
            "id": user.id,
            "username": user.username,
            "email": user.decrypted_email,
            "is_active": user.is_active,
            "email_verified": user.email_verified,
            "date_joined": user.date_joined.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "is_fortytwo_user": user.is_fortytwo_user,
            "profile_image": profile_image_url,
            "fortytwo_image": user.fortytwo_image,
        }
        return data

    @staticmethod
    def delete_user_account(user, password=None):
        """Manages account deletion"""
        # Disclaimer!
		# This method is not used in the current implementation of the project
        # because we use GDPR deletion instead (softer deletion)
		# This is used in the 8000 port development environment but was deprecated in production
        # We keep it here for reference purposes and avoid errors when is called when the project is running
        try:
            if not user.is_fortytwo_user:
                if not password or not user.check_password(password):
                    raise ValidationError("Contraseña incorrecta")
            
            # First delete user sessions
            UserSession.objects.filter(user=user).delete()
            
            # Then we delete the user data
            GDPRService.delete_user_data(user)
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user account: {str(e)}")
            raise ValidationError(f"Error al eliminar la cuenta: {str(e)}")
