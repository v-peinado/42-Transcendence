# authentication/fortytwo_auth/views.py
from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from .services.fortytwo_service import FortyTwoAuthService

# Vistas y lógica compartida
class FortyTwoAuth:
    @staticmethod
    def get_auth_url():
        service = FortyTwoAuthService()
        return service.get_authorization_url()
    
    @staticmethod
    def process_callback(code):
        service = FortyTwoAuthService()
        token_data = service.get_access_token(code)
        user_data = service.get_user_info(token_data['access_token'])
        return service.get_or_create_user(user_data)

# Vistas Web y API combinadas
def fortytwo_login(request):
    return redirect(FortyTwoAuth.get_auth_url())

def fortytwo_callback(request):
    code = request.GET.get('code')
    try:
        user = FortyTwoAuth.process_callback(code)
        login(request, user)
        messages.success(request, 'Login exitoso con 42')
        return redirect('user')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('login')

class FortyTwoAuthAPIView(APIView):
    def get(self, request):
        auth_url = FortyTwoAuth.get_auth_url()
        return Response({'auth_url': auth_url})

class FortyTwoCallbackAPIView(APIView):
    def get(self, request):
        code = request.GET.get('code')
        try:
            user = FortyTwoAuth.process_callback(code)
            return Response({
                'status': 'success',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            })
        except Exception as e:
            return Response({'error': str(e)}, status=400)