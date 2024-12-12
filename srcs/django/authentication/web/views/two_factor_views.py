from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseNotAllowed
from ...services.two_factor_service import TwoFactorService
from ...models import CustomUser

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