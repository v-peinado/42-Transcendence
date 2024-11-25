from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from .services.fortytwo_service import FortyTwoAuthService
from django.conf import settings
from ..models import CustomUser
from django.http import HttpResponseRedirect
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone
from ..web.utils import (
    generate_2fa_code, 
    send_2fa_code, 
    verify_2fa_code,
    generate_jwt_token 
)
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

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
                    'is_active': False,  # Usuario inactivo hasta verificar email
                    'email_verified': False  # Email no verificado inicialmente
                }
            )

            # Si es un usuario nuevo, enviar email de verificación
            if created:
                # Generar token JWT
                token = generate_jwt_token(user)
                user.email_verification_token = token
                user.save()
                
                # Preparar y enviar email de verificación
                subject = 'Verifica tu cuenta de PongOrama'
                message = render_to_string('authentication/email_verification.html', {
                    'user': user,
                    'domain': settings.SITE_URL,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': token,
                    'protocol': 'https'
                })
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                    html_message=message
                )
                
            return user, created

        except Exception as e:
            print(f"Error detallado en process_callback: {str(e)}")
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
        return redirect('login')
    
    try:
        user, is_new_user = FortyTwoAuth.process_callback(code)
        if user:
            if not user.email_verified:
                messages.warning(request, 'Verifica tu email para acceder a tu cuenta')
                return redirect('login')
                
            if user.two_factor_enabled:
                # Guardar datos en sesión
                request.session['pending_user_id'] = user.id
                request.session['user_authenticated'] = True
                request.session['fortytwo_user'] = True
                
                # Generar y enviar código 2FA
                code = generate_2fa_code(user)
                send_2fa_code(user, code)
                
                # Redirigir a verificación 2FA
                return redirect('verify_2fa')
                
            auth_login(request, user)
            return redirect('user')
    except Exception as e:
        messages.error(request, f'Error en la autenticación: {str(e)}')
        return redirect('login')

def verify_2fa(request):
    user_id = request.session.get('pending_user_id')
    user_authenticated = request.session.get('user_authenticated', False)
    is_fortytwo = request.session.get('fortytwo_user', False)
    is_manual = request.session.get('manual_user', False)
    
    if not user_id or not user_authenticated:
        messages.error(request, 'Sesión inválida')
        return redirect('login')
        
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        for key in ['pending_user_id', 'user_authenticated', 'fortytwo_user', 'manual_user']:
            if key in request.session:
                del request.session[key]
        return redirect('login')

    if request.method == 'POST':
        code = request.POST.get('code')
        
        if verify_2fa_code(user, code):
            for key in ['pending_user_id', 'user_authenticated', 'fortytwo_user', 'manual_user']:
                if key in request.session:
                    del request.session[key]
                    
            auth_login(request, user)
            messages.success(request, 'Inicio de sesión exitoso')
            return redirect('user')
        else:
            messages.error(request, 'Código inválido o expirado')
            
    return render(request, 'authentication/verify_2fa.html')

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
            
            if user.two_factor_enabled:
                # Generar y enviar código 2FA
                code = generate_2fa_code(user)
                send_2fa_code(user, code)
                
                # Guardar ID de usuario en sesión
                request.session['pending_user_id'] = user.id
                
                return Response({
                    'status': 'pending_2fa',
                    'message': 'Por favor, verifica el código enviado a tu email'
                }, status=200)
            
            auth_login(request, user)
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