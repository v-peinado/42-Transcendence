from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_bytes 
from django.conf import settings
from django.template.loader import render_to_string  
from django.utils.html import strip_tags 
from ...services.two_factor_service import TwoFactorService
from ...services.auth_service import AuthenticationService
from ...services.token_service import TokenService
from ...services.email_service import EmailService 
from ...models import CustomUser
import qrcode
import io
import json

def verify_email(request, uidb64, token):
    """Vista para verificar email"""
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = CustomUser.objects.get(pk=uid)
        payload = TokenService.decode_jwt_token(token)
        
        if user and payload and payload['user_id'] == user.id:
            user.email_verified = True
            user.is_active = True
            user.email_verification_token = None
            user.save()
            
            # Enviar email de bienvenida usando EmailService
            EmailService.send_welcome_email(user)
            
            messages.success(request, "Tu cuenta ha sido verificada correctamente. Ahora puedes iniciar sesión")
            return redirect('login')
        else:
            messages.error(request, "El enlace de verificación no es válido")
            return redirect('login')
            
    except Exception as e:
        messages.error(request, str(e))
        return redirect('login')

def verify_email_change(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = CustomUser.objects.get(pk=uid)
        payload = TokenService.decode_jwt_token(token)
        
        if user and payload and payload['user_id'] == user.id and token == user.pending_email_token:
            old_email = user.email
            user.email = user.pending_email
            user.pending_email = None
            user.pending_email_token = None
            user.save()

            # Enviar email de confirmación usando EmailService
            EmailService.send_email_change_confirmation(user, old_email)
            
            messages.success(request, 'Tu email ha sido actualizado correctamente')
            return redirect('edit_profile')
            
        messages.error(request, 'El enlace de verificación no es válido')
        return redirect('edit_profile')
        
    except Exception as e:
        messages.error(request, str(e))
        return redirect('edit_profile')

@login_required
def enable_2fa(request):
    """Vista para activar 2FA"""
    if request.method == 'POST':
        try:
            user = request.user
            user.two_factor_enabled = True
            if not user.two_factor_secret:
                user.two_factor_secret = TwoFactorService.generate_2fa_secret()
            user.save()
            
            messages.success(request, '2FA activado correctamente')
            return redirect('user')
            
        except Exception as e:
            messages.error(request, str(e))
            return redirect('user')
            
    return render(request, 'authentication/enable_2fa.html')

def verify_2fa(request):
    """Vista para verificar código 2FA"""
    # Verificar autenticación previa
    user_id = request.session.get('pending_user_id')
    user_authenticated = request.session.get('user_authenticated', False)
    
    if not user_id or not user_authenticated:
        messages.error(request, 'Sesión inválida')
        return redirect('login')
    
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        # Limpiar sesión
        for key in ['pending_user_id', 'user_authenticated', 'fortytwo_user', 'manual_user']:
            if key in request.session:
                del request.session[key]
        return redirect('login')

    if request.method == 'POST':
        code = request.POST.get('code')
        
        if TwoFactorService.verify_2fa_code(user, code):
            # Limpiar sesión y hacer login
            for key in ['pending_user_id', 'user_authenticated', 'fortytwo_user', 'manual_user']:
                if key in request.session:
                    del request.session[key]
                    
            auth_login(request, user)
            messages.success(request, 'Inicio de sesión exitoso')
            return redirect('user')
        else:
            messages.error(request, 'Código inválido o expirado')
            
    return render(request, 'authentication/verify_2fa.html')

@login_required
def disable_2fa(request):
    """Vista para desactivar 2FA"""
    if request.method == 'POST':
        try:
            TwoFactorService.disable_2fa(request.user)
            messages.success(request, '2FA desactivado correctamente')
            return redirect('user')
        except Exception as e:
            messages.error(request, str(e))
            return redirect('user')
    return HttpResponseNotAllowed(['POST'])

@login_required
def generate_qr(request, username):
    """Vista para generar código QR"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(username)
    qr.make(fit=True)
    
    img = qr.make_image(fill='black', back_color='white')
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    
    return HttpResponse(buffer.getvalue(), content_type="image/png")

@csrf_exempt
def validate_qr(request):
    """Vista para validar código QR"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            
            if not username:
                return JsonResponse({'success': False, 'error': 'Código QR inválido'})
                
            user = CustomUser.objects.filter(username=username).first()
            
            if user:
                if not user.email_verified:
                    return JsonResponse({
                        'success': False, 
                        'error': 'Por favor verifica tu email para activar tu cuenta'
                    })
                
                if user.two_factor_enabled:
                    # Guardar datos en sesión
                    request.session['pending_user_id'] = user.id
                    request.session['user_authenticated'] = True
                    request.session['manual_user'] = not user.is_fortytwo_user
                    request.session['fortytwo_user'] = user.is_fortytwo_user
                    
                    # Generar y enviar código 2FA
                    code = TwoFactorService.generate_2fa_code(user)
                    TwoFactorService.send_2fa_code(user, code)
                    
                    return JsonResponse({
                        'success': True,
                        'require_2fa': True,
                        'redirect_url': '/verify-2fa/',
                        'message': 'Código 2FA enviado a tu email'
                    })
                
                # Si no tiene 2FA, login directo
                auth_login(request, user)
                return JsonResponse({
                    'success': True,
                    'redirect_url': '/user/'
                })
            else:
                return JsonResponse({
                    'success': False, 
                    'error': 'Usuario no encontrado'
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False, 
                'error': 'Datos inválidos'
            })
            
    return JsonResponse({
        'success': False, 
        'error': 'Método no permitido'
    })