from django.shortcuts import redirect
from django.contrib import messages
from ...services.mail_service import EmailVerificationService

def verify_email(request, uidb64, token):
    """Vista para verificación de email"""
    try:
        EmailVerificationService.verify_email(uidb64, token)
        messages.success(request, "Tu cuenta ha sido verificada correctamente.")
    except ValueError as e:
        messages.error(request, str(e))
    return redirect('login')

def verify_email_change(request, uidb64, token):
    """Vista para verificación de cambio de email"""
    try:
        EmailVerificationService.verify_email_change(uidb64, token)
        messages.success(request, 'Tu email ha sido actualizado correctamente')
    except ValueError as e:
        messages.error(request, str(e))
    return redirect('edit_profile')

# Vistas para generar y validar códigos QR

# @login_required
# def generate_qr(request, username):
#     """Vista para generar código QR"""
#     if not request.user.is_authenticated:							# Si el usuario no está autenticado...
#         return redirect('login')
    
#     qr = qrcode.QRCode(version=1, box_size=10, border=4)			# Crear objeto QR (versión, tamaño de caja, borde)
#     qr.add_data(username)											# Agregar datos al QR
#     qr.make(fit=True)												# Ajustar QR al tamaño
    
#     img = qr.make_image(fill='black', back_color='white')			# Crear imagen del QR (color de relleno, color de fondo)
#     buffer = io.BytesIO()											# Buffer para almacenar imagen
#     img.save(buffer, format="PNG")									# Guardar imagen en el buffer
#     buffer.seek(0)													# Mover el cursor al inicio del buffer (para leerlo)
    
#     return HttpResponse(buffer.getvalue(), content_type="image/png")

# @csrf_exempt														# Deshabilitar CSRF (Es un token de seguridad para evitar ataques CSRF, consiste en enviar una solicitud desde un sitio web malicioso)
# def validate_qr(request):
#     """Validar código QR"""
#     if request.method == 'POST':									# Si se envía un formulario
#         try:
#             data = json.loads(request.body)							# Cargar datos del cuerpo de la solicitud
#             username = data.get('username')							# Obtener nombre de usuario del formulario
            
#             if not username:
#                 return JsonResponse({'success': False, 'error': 'Código QR inválido'})
                
#             user = CustomUser.objects.filter(username=username).first()
            
#             if user:
#                 if not user.email_verified:
#                     return JsonResponse({
#                         'success': False, 
#                         'error': 'Por favor verifica tu email para activar tu cuenta'
#                     })
                
#                 if user.two_factor_enabled:
#                     # Guardar datos en sesión
#                     request.session['pending_user_id'] = user.id
#                     request.session['user_authenticated'] = True
#                     request.session['manual_user'] = not user.is_fortytwo_user
#                     request.session['fortytwo_user'] = user.is_fortytwo_user
                    
#                     # Generar y enviar código 2FA
#                     code = TwoFactorService.generate_2fa_code(user)
#                     TwoFactorService.send_2fa_code(user, code)
                    
#                     return JsonResponse({
#                         'success': True,
#                         'require_2fa': True,
#                         'redirect_url': '/verify-2fa/',
#                         'message': 'Código 2FA enviado a tu email'
#                     })
                
#                 # Si no tiene 2FA, login directo
#                 auth_login(request, user)
#                 return JsonResponse({
#                     'success': True,
#                     'redirect_url': '/user/'
#                 })
#             else:
#                 return JsonResponse({
#                     'success': False, 
#                     'error': 'Usuario no encontrado'
#                 })
                
#         except json.JSONDecodeError:
#             return JsonResponse({
#                 'success': False, 
#                 'error': 'Datos inválidos'
#             })
            
#     return JsonResponse({
#         'success': False, 
#         'error': 'Método no permitido'
#     })