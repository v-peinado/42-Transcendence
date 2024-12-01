from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from django.utils import timezone
from ..models import CustomUser
import pyotp
import time

class TwoFactorService:
    @staticmethod
    def generate_2fa_secret():
        """Genera un nuevo secreto para 2FA"""
        return pyotp.random_base32()

    @staticmethod
    def generate_2fa_code(user):
        """Genera un código 2FA temporal"""
        try:
            # Verificar si el usuario es válido
            if not user:
                raise ValueError("Usuario no proporcionado")
                
            # Si nos pasan un ID en lugar del objeto usuario
            if not isinstance(user, CustomUser):
                try:
                    user = CustomUser.objects.get(id=user)
                except CustomUser.DoesNotExist:
                    raise ValueError("Usuario no encontrado")

            # Generar código 2FA
            if not user.two_factor_secret:
                user.two_factor_secret = TwoFactorService.generate_2fa_secret()
                
            totp = pyotp.TOTP(user.two_factor_secret)
            code = totp.now()
            
            # Guardar código y timestamp
            user.last_2fa_code = code
            user.last_2fa_time = timezone.now()
            user.save()
            
            return code
            
        except Exception as e:
            raise ValueError(f"Error al generar código 2FA: {str(e)}")

    @staticmethod
    def verify_2fa_code(user, code):
        """Verifica si el código 2FA es válido"""
        # Verificar que user sea un objeto CustomUser
        if not isinstance(user, CustomUser):
            try:
                user = CustomUser.objects.get(id=user)
            except (ValueError, CustomUser.DoesNotExist):
                return False

        try:
            if not user.two_factor_secret or not code:
                return False
                
            time_diff = timezone.now() - user.last_2fa_time
            if time_diff.total_seconds() > 300:  # 5 minutos
                return False
                
            return user.last_2fa_code == code
            
        except Exception:
            return False

    @staticmethod
    def send_2fa_code(user, code):
        """Envía el código 2FA por email"""
        subject = 'Tu código de verificación PongOrama'
        context = {
            'user': user,
            'code': code
        }
        html_message = render_to_string('authentication/2fa_email.html', context)
        
        send_mail(
            subject,
            strip_tags(html_message),
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False
        )

    @staticmethod
    def enable_2fa(user):
        """Habilita 2FA para un usuario"""
        try:
            # Generar código
            code = TwoFactorService.generate_2fa_code(user)
            
            # Activar 2FA para el usuario
            user.two_factor_enabled = True
            user.save()
            
            # Enviar código por email
            TwoFactorService.send_2fa_code(user, code)
            
            return code
            
        except Exception as e:
            raise ValueError(f"Error al activar 2FA: {str(e)}")

    @staticmethod
    def disable_2fa(user):
        """Deshabilita 2FA para un usuario"""
        user.two_factor_enabled = False
        user.two_factor_secret = None
        user.save()
        return True