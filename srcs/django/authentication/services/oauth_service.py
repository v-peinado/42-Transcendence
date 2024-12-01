from django.conf import settings
from django.core.exceptions import ValidationError
import requests
from ..models import CustomUser

class OAuth42Service:
    @staticmethod
    def get_authorization_url():
        """Obtener URL de autorización de 42"""
        try:
            return (
                f"https://api.intra.42.fr/oauth/authorize"
                f"?client_id={settings.FORTYTWO_CLIENT_ID}"
                f"&redirect_uri={settings.FORTYTWO_REDIRECT_URI}"
                f"&response_type=code"
                f"&scope=public"
            )
        except Exception as e:
            raise ValidationError(f"Error al generar URL de autorización: {str(e)}")

    @staticmethod
    def get_access_token(code):
        """Obtener token de acceso usando código de autorización"""
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
        """Obtener información del usuario desde la API de 42"""
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(
                'https://api.intra.42.fr/v2/me',
                headers=headers
            )
            
            if response.status_code != 200:
                raise ValidationError("Error al obtener información de usuario")
                
            return response.json()
            
        except Exception as e:
            raise ValidationError(f"Error al obtener información de usuario: {str(e)}")

    @staticmethod
    def create_or_update_user(user_info):
        """Crear o actualizar usuario con datos de 42"""
        try:
            fortytwo_id = str(user_info.get('id'))
            email = user_info.get('email')
            login = user_info.get('login')
            image_url = user_info.get('image_url')
            
            user, created = CustomUser.objects.get_or_create(
                fortytwo_id=fortytwo_id,
                defaults={
                    'username': f'42.{login}',
                    'email': email,
                    'is_fortytwo_user': True,
                    'is_active': True,
                    'email_verified': True,
                    'fortytwo_image': image_url
                }
            )
            
            if not created:
                # Actualizar datos existentes
                user.email = email
                user.fortytwo_image = image_url
                user.save()
                
            return user, created
            
        except Exception as e:
            raise ValidationError(f"Error al procesar usuario de 42: {str(e)}")

    @staticmethod
    def process_oauth_callback(code):
        """Procesar callback completo de OAuth"""
        try:
            access_token = OAuth42Service.get_access_token(code)
            user_info = OAuth42Service.get_user_info(access_token)
            return OAuth42Service.create_or_update_user(user_info)
        except Exception as e:
            raise ValidationError(f"Error en proceso OAuth: {str(e)}")