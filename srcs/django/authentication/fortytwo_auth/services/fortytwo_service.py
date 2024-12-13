import requests
from django.conf import settings
from authentication.services.token_service import TokenService
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from authentication.services.mail_service import MailSendingService 
from authentication.services.two_factor_service import TwoFactorService
from authentication.models import CustomUser
from django.contrib.auth import login as auth_login

class FortyTwoAuth:
    @staticmethod
    def get_auth_url(is_api=False):
        service = FortyTwoAuthService(is_api=is_api)
        return service.get_authorization_url()
    
    @staticmethod
    def process_callback(code, is_api=False):
        try:
            service = FortyTwoAuthService(is_api=is_api)
            token_data = service.get_access_token(code)
            user_data = service.get_user_info(token_data['access_token'])
            
            # Obtener o crear usuario
            user, created = CustomUser.objects.get_or_create(
                username=f"42.{user_data['login']}",
                defaults={
                    'email': user_data['email'],
                    'fortytwo_id': str(user_data['id']),
                    'is_fortytwo_user': True,
                    'is_active': False,
                    'email_verified': False,
                    'fortytwo_image': user_data.get('image', {}).get('link')
                }
            )

            # Usuario nuevo: enviar email verificación
            if created:
                token = TokenService.generate_auth_token(user)
                user.email_verification_token = token
                user.save()
                
                MailSendingService.send_verification_email(user, {
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': token
                })

            # Si tiene 2FA, generar código
            if user.two_factor_enabled:
                code = TwoFactorService.generate_2fa_code(user)
                TwoFactorService.send_2fa_code(user, code)

            return user, created

        except Exception as e:
            print(f"Error en process_callback: {str(e)}")
            raise

class FortyTwoAuthService:
    AUTH_URL = 'https://api.intra.42.fr/oauth/authorize'
    TOKEN_URL = 'https://api.intra.42.fr/oauth/token'
    USER_URL = 'https://api.intra.42.fr/v2/me'
    
    def __init__(self, is_api=False):
        if is_api:
            self.client_id = settings.FORTYTWO_API_UID
            self.client_secret = settings.FORTYTWO_API_SECRET
            self.redirect_uri = settings.FORTYTWO_API_URL
        else:
            self.client_id = settings.FORTYTWO_CLIENT_ID
            self.client_secret = settings.FORTYTWO_CLIENT_SECRET
            self.redirect_uri = settings.FORTYTWO_REDIRECT_URI

    def get_authorization_url(self):
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'public'
        }
        print(f"Authorization URL params: {params}")  # Debug
        return f"{self.AUTH_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"

    def get_access_token(self, code):
        data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.redirect_uri
        }
        
        print(f"Token request data: {data}")  # Debug
        
        response = requests.post(self.TOKEN_URL, data=data)
        
        print(f"Token response status: {response.status_code}")  # Debug
        print(f"Token response: {response.text}")  # Debug
        
        if response.status_code != 200:
            raise Exception(f"Failed to get access token from 42: {response.text}")
            
        return response.json()

    def get_user_info(self, access_token):
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(self.USER_URL, headers=headers)
        
        print(f"User info response status: {response.status_code}")  # Debug
        print(f"User info response: {response.text}")  # Debug
        
        if response.status_code != 200:
            raise Exception("Failed to get user info from 42")
            
        return response.json()

    @staticmethod
    def handle_login(request, is_api=False):
        try:
            auth_url = FortyTwoAuth.get_auth_url(is_api=is_api)
            return True, auth_url, None
        except Exception as e:
            return False, None, str(e)

    @staticmethod
    def handle_callback(request, is_api=False):
        code = request.GET.get('code')
        if not code:
            return False, None, 'No se proporcionó código de autorización'

        try:
            user, created = FortyTwoAuth.process_callback(code, is_api=is_api)

            if not user.email_verified:
                return False, user, 'Verifica tu email para acceder a tu cuenta'

            if user.two_factor_enabled:
                code = TwoFactorService.generate_2fa_code(user)
                TwoFactorService.send_2fa_code(user, code)
                request.session.update({
                    'pending_user_id': user.id,
                    'user_authenticated': True,
                    'fortytwo_user': True
                })
                return True, user, 'pending_2fa'

            auth_login(request, user)
            return True, user, None

        except Exception as e:
            return False, None, str(e)