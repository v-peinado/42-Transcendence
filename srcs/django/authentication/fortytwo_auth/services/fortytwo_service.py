# authentication/fortytwo_auth/services/fortytwo_service.py
import requests
from django.conf import settings
from django.contrib.auth.models import User

class FortyTwoAuthService:
    AUTH_URL = 'https://api.intra.42.fr/oauth/authorize'
    TOKEN_URL = 'https://api.intra.42.fr/oauth/token'
    USER_URL = 'https://api.intra.42.fr/v2/me'
    
    def __init__(self):
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
        return f"{self.AUTH_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"

    def get_access_token(self, code):
        data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.redirect_uri
        }
        response = requests.post(self.TOKEN_URL, data=data)
        return response.json()

    def get_user_info(self, access_token):
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(self.USER_URL, headers=headers)
        return response.json()

    def get_or_create_user(self, user_data):
        try:
            user = User.objects.get(email=user_data['email'])
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=user_data['login'],
                email=user_data['email']
            )
        return user