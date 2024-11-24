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
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from .utils import generate_jwt_token, decode_jwt_token 
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

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
                
            # Obtener o crear usuario
            user, created = CustomUser.objects.get_or_create(
                username=f"42.{user_data['login']}",
                defaults={
                    'email': user_data['email'],
                    'fortytwo_id': str(user_data['id']),
                    'is_fortytwo_user': True,
                    'fortytwo_image': fortytwo_image,
                    'is_active': False,
                    'email_verified': False
                }
            )
            
            if created:
                # Generar token JWT
                token = generate_jwt_token(user)
                user.email_verification_token = token
                user.save()
                
                # Email de verificación
                subject = 'Verifica tu cuenta de PongOrama'
                message = render_to_string('authentication/email_verification.html', {
                    'user': user,
                    'domain': settings.SITE_URL,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': token,
                    'protocol': 'https'
                })
                
                # Enviar el email - Esta es la línea que faltaba
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                
            return user, created

        except Exception as e:
            print(f"Error en process_callback: {str(e)}")
            raise

# Vista Web para login con 42
def fortytwo_login(request):
    try:
        auth_url = FortyTwoAuth.get_auth_url()
        return redirect(auth_url)
    except Exception as e:
        messages.error(request, f'Error al iniciar la autenticación: {str(e)}')
        return redirect('login')

# Vista Web para callback de 42
def fortytwo_callback(request):
    code = request.GET.get('code')
    if not code:
        messages.error(request, 'No se recibió código de autorización')
        return redirect('login')
    
    try:
        user, is_new_user = FortyTwoAuth.process_callback(code)
        if user:
            # Verificar si el usuario ha validado su email
            if not user.email_verified:
                messages.warning(
                    request,
                    'Tu cuenta aún no está verificada. Por favor, revisa tu correo '
                    'electrónico y sigue las instrucciones para activar tu cuenta.'
                )
                return redirect('login')
                
            login(request, user)
            if is_new_user:
                messages.success(
                    request, 
                    '¡Bienvenido! Tu cuenta con 42 ha sido creada exitosamente.'
                )
            else:
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
            user, is_new = FortyTwoAuth.process_callback(code, is_api=True)
            
            # Verificar si el usuario ha validado su email
            if not user.email_verified:
                return Response({
                    'error': 'Tu cuenta aún no está verificada. Por favor, revisa tu correo '
                            'electrónico y sigue las instrucciones para activar tu cuenta.'
                }, status=403)
            
            login(request, user)
            return Response({
                'status': 'success',
                'message': 'Login successful',
                'user': {
                    'username': user.username,
                    'email': user.email
                }
            })

        except Exception as e:
            print(f"Error en callback: {str(e)}")
            return Response({'error': str(e)}, status=400)