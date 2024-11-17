from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from .services.fortytwo_service import FortyTwoAuthService
from django.conf import settings
from ..models import CustomUser
from django.http import HttpResponseRedirect
import json

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
            
            # Obtener la URL de la imagen de 42
            fortytwo_image = None
            if user_data.get('image'):
                fortytwo_image = user_data['image']['versions'].get('large') or user_data['image']['link']

            user, created = CustomUser.objects.get_or_create(
                username=user_data['login'],
                defaults={
                    'email': user_data['email'],
                    'fortytwo_id': str(user_data['id']),
                    'is_fortytwo_user': True,
                    'fortytwo_image': fortytwo_image  # Guardar la URL de la imagen de 42
                }
            )

            if not created and not user.fortytwo_image:
                user.fortytwo_image = fortytwo_image
                user.save()

            return user
        except Exception as e:
            print("Error in process_callback:", str(e))
            raise

# Vista Web para login con 42
def fortytwo_login(request):
    return redirect(FortyTwoAuth.get_auth_url())

# Vista Web para callback de 42
def fortytwo_callback(request):
    code = request.GET.get('code')
    try:
        user = FortyTwoAuth.process_callback(code)
        login(request, user)
        messages.success(request, 'Login exitoso con 42')
        return redirect('user')
    except Exception as e:
        messages.error(request, f'Error en la autenticación: {str(e)}')
        return redirect('login')

# Vistas API
class FortyTwoAuthAPIView(APIView):
    def get(self, request):
        auth_url = FortyTwoAuth.get_auth_url(is_api=True)
        return Response({'auth_url': auth_url})

class FortyTwoCallbackAPIView(APIView):
    def get(self, request):
        code = request.GET.get('code')
        if not code:
            return Response({'error': 'No code provided'}, status=400)

        try:
            user = FortyTwoAuth.process_callback(code, is_api=True)
            login(request, user)
            
            # Crear una respuesta de redirección
            response = HttpResponseRedirect('/user.html')
            
            # Añadir los datos del usuario como headers
            response['X-User-Data'] = json.dumps({
                'username': user.username,
                'email': user.email,
                'profile_image': user.profile_image
            })
            
            return response

        except Exception as e:
            print(f"Error en callback: {str(e)}")
            return HttpResponseRedirect('/login.html')