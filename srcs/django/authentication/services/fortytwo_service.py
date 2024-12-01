from django.conf import settings
from django.core.exceptions import ValidationError
from ..models import CustomUser
import requests

class FortyTwoService:
    @staticmethod
    def get_authorization_url():
        """Obtener URL de autorización de 42"""
        try:
            return (
                f"https://api.intra.42.fr/oauth/authorize"
                f"?client_id={settings.FORTYTWO_CLIENT_ID}"
                f"&redirect_uri={settings.FORTYTWO_REDIRECT_URI}"
                f"&response_type=code"
            )
        except Exception as e:
            raise ValidationError(f"Error al generar URL de autorización: {str(e)}")

    @staticmethod
    def get_access_token(code):
        """Obtener token de acceso usando el código de autorización"""
        try:
            response = requests.post(
                'https://api.intra.42.fr/oauth/token',
                data={
                    'grant_type': 'authorization_code',
                    'client_id': settings.FORTYTWO_CLIENT_ID,
                    'client_secret': settings.FORTYTWO_CLIENT_SECRET,
                    'code': code,
                    'redirect_uri': settings.FORTYTWO_REDIRECT_URI
                }
            )
            
            if response.status_code != 200:
                raise ValidationError("Error al obtener token de acceso")
                
            return response.json().get('access_token')
            
        except Exception as e:
            raise ValidationError(f"Error en proceso de obtención de token: {str(e)}")

    @staticmethod
    def get_user_info(access_token):
        """Obtener información del usuario de 42"""
        try:
            response = requests.get(
                'https://api.intra.42.fr/v2/me',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            if response.status_code != 200:
                raise ValidationError("Error al obtener información de usuario")
                
            return response.json()
            
        except Exception as e:
            raise ValidationError(f"Error al obtener información de usuario: {str(e)}")

    @staticmethod
    def process_callback(code):
        """Procesar callback de 42 y crear/actualizar usuario"""
        try:
            # Obtener token de acceso
            access_token = FortyTwoService.get_access_token(code)
            
            # Obtener información del usuario
            user_info = FortyTwoService.get_user_info(access_token)
            
            # Datos básicos del usuario
            username = f"42.{user_info.get('login')}"
            email = user_info.get('email')
            fortytwo_id = str(user_info.get('id'))
            fortytwo_image = user_info.get('image_url')
            
            # Buscar usuario existente
            user = CustomUser.objects.filter(fortytwo_id=fortytwo_id).first()
            created = False
            
            if not user:
                # Crear nuevo usuario
                user = CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    fortytwo_id=fortytwo_id,
                    is_fortytwo_user=True,
                    is_active=True,
                    email_verified=True
                )
                user.fortytwo_image = fortytwo_image
                user.save()
                created = True
            else:
                # Actualizar datos existentes
                user.email = email
                user.fortytwo_image = fortytwo_image
                user.save()
                
            return user, created
            
        except Exception as e:
            raise ValidationError(f"Error en proceso de callback: {str(e)}")