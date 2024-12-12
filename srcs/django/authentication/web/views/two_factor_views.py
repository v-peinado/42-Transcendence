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
            TwoFactorService.enable_2fa(request.user)
            messages.success(request, '2FA activado correctamente')	# Mostrar mensaje de éxito
            return redirect('user')
        except Exception as e:										# Capturar cualquier excepción de TwoFactorService
            messages.error(request, str(e))
            return redirect('user')
    return render(request, 'authentication/enable_2fa.html')

def verify_2fa(request):
    """Verificar 2FA cuando queremos iniciar sesión"""
    is_valid, user = TwoFactorService.verify_session(
        request.session.get('pending_user_id'),
        request.session.get('user_authenticated', False)
    )

    if not is_valid:
        messages.error(request, 'Sesión inválida')
        return redirect('login')

    if request.method == 'POST':									# Si se envía un formulario
        code = request.POST.get('code')								# Obtener código 2FA del formulario
        if TwoFactorService.verify_2fa_code(user, code):			# Si el código es válido...
            TwoFactorService.clean_session_keys(request.session)
            auth_login(request, user)
            messages.success(request, 'Inicio de sesión exitoso')
            return redirect('user')
        messages.error(request, 'Código inválido')

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