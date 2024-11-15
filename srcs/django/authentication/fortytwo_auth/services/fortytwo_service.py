# authentication/fortytwo_auth/services/fortytwo_service.py
import requests
from django.conf import settings
from authentication.models import CustomUser

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