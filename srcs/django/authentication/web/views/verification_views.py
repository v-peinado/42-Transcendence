from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.http import urlsafe_base64_decode
from ...services.two_factor_service import TwoFactorService
from ...services.token_service import TokenService
from ...services.email_service import EmailService 
from ...models import CustomUser
import qrcode
import io
import json

def verify_email(request, uidb64, token):
    """Enviar email de verificación(bienvenida)"""
    try:
        uid = urlsafe_base64_decode(uidb64).decode()				# Decodificar ID de usuario (base64)
        user = CustomUser.objects.get(pk=uid)						# Obtener usuario por ID
        payload = TokenService.decode_jwt_token(token)				# Decodificar token JWT
        
        if user and payload and payload['user_id'] == user.id:		# Si el usuario y el token son válidos...
            user.email_verified = True								# Marcar email como verificado
            user.is_active = True									# Marcar usuario como activo
            user.email_verification_token = None					# Limpiar token de verificación
            user.save()
            
            # Enviar email de bienvenida usando EmailService
            EmailService.send_welcome_email(user)	
            
            messages.success(request, "Tu cuenta ha sido verificada correctamente. Ahora puedes iniciar sesión")
            return redirect('login')
        else:
            messages.error(request, "El enlace de verificación no es válido")
            return redirect('login')
            
    except Exception as e:											# Capturar cualquier excepción (de TokenService o CustomUser)
        messages.error(request, str(e))
        return redirect('login')

def verify_email_change(request, uidb64, token):
    """Enviar email de verificación para cambio de email"""			
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = CustomUser.objects.get(pk=uid)
        payload = TokenService.decode_jwt_token(token)
        
        if user and payload and payload['user_id'] == user.id and token == user.pending_email_token:	# ...como ariba, pero se comprueba el token de email pendiente
            old_email = user.email									# Guardar email actual (para el email de confirmación)
            user.email = user.pending_email							# Actualizar email
            user.pending_email = None								# Limpiar email pendiente
            user.pending_email_token = None							# Limpiar token de email pendiente
            user.save()												# Guardar cambios

            # Enviar email con enlace de confirmación a la dirección antigua antes de cambiarla
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
    """Activar 2FA a traves de editar perfil"""
    if request.method == 'POST':									# Si se envía un formulario
        try:
            user = request.user										# Obtener usuario autenticado
            user.two_factor_enabled = True							# Habilitar 2FA
            if not user.two_factor_secret:							# Si no tiene un secreto 2FA...
                user.two_factor_secret = TwoFactorService.generate_2fa_secret()
            user.save()			
            
            messages.success(request, '2FA activado correctamente')	# Mostrar mensaje de éxito
            return redirect('user')
            
        except Exception as e:										# Capturar cualquier excepción de TwoFactorService
            messages.error(request, str(e))
            return redirect('user')
            
    return render(request, 'authentication/enable_2fa.html')

def verify_2fa(request):
    """Verificar 2FA cuando queremos iniciar sesión"""
    user_id = request.session.get('pending_user_id')				# Obtener ID de usuario de la sesión
    user_authenticated = request.session.get('user_authenticated', False)	# Verificar si el usuario está autenticado
    
    if not user_id or not user_authenticated:						# Si no hay ID de usuario o no está autenticado...
        messages.error(request, 'Sesión inválida')					# Mostrar mensaje de error
        return redirect('login')
    
    try:
        user = CustomUser.objects.get(id=user_id)					# Obtener usuario por ID
    except CustomUser.DoesNotExist:									# Si el usuario no existe...
        messages.error(request, 'Usuario no encontrado')			# Mostrar mensaje de error
        for key in ['pending_user_id', 'user_authenticated', 'fortytwo_user', 'manual_user']:	# Limpiar todas las claves de la sesión
            if key in request.session:								# Si la clave está en la sesión...
                del request.session[key]							# Eliminar la clave de la sesión
        return redirect('login')

    if request.method == 'POST':									# Si se envía un formulario
        code = request.POST.get('code')								# Obtener código 2FA del formulario
        
        if TwoFactorService.verify_2fa_code(user, code):			# Si el código es válido...
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
    """Desactivar 2FA a través de editar perfil"""
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
    if not request.user.is_authenticated:							# Si el usuario no está autenticado...
        return redirect('login')
    
    qr = qrcode.QRCode(version=1, box_size=10, border=4)			# Crear objeto QR (versión, tamaño de caja, borde)
    qr.add_data(username)											# Agregar datos al QR
    qr.make(fit=True)												# Ajustar QR al tamaño
    
    img = qr.make_image(fill='black', back_color='white')			# Crear imagen del QR (color de relleno, color de fondo)
    buffer = io.BytesIO()											# Buffer para almacenar imagen
    img.save(buffer, format="PNG")									# Guardar imagen en el buffer
    buffer.seek(0)													# Mover el cursor al inicio del buffer (para leerlo)
    
    return HttpResponse(buffer.getvalue(), content_type="image/png")

@csrf_exempt														# Deshabilitar CSRF (Es un token de seguridad para evitar ataques CSRF, consiste en enviar una solicitud desde un sitio web malicioso)
def validate_qr(request):
    """Validar código QR"""
    if request.method == 'POST':									# Si se envía un formulario
        try:
            data = json.loads(request.body)							# Cargar datos del cuerpo de la solicitud
            username = data.get('username')							# Obtener nombre de usuario del formulario
            
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