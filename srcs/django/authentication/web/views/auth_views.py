from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.core.exceptions import ValidationError
from authentication.services.auth_service import AuthenticationService
from authentication.services.email_service import EmailService
from authentication.services.token_service import TokenService
from authentication.services.password_service import PasswordService
from authentication.forms.auth_forms import RegistrationForm
from authentication.services.two_factor_service import TwoFactorService
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.utils.html import escape

def home(request):
    """Vista principal"""
    return render(request, 'authentication/home.html')

def login(request):
    """Vista de inicio de sesión para usuarios registrados de forma manual"""												
    if request.method == 'POST':											# Si se envía un formulario
        username = request.POST.get('username').strip().lower()
        password = request.POST.get('password')
        remember = request.POST.get('remember', None)

        user = authenticate(request, username=username, password=password)	# Autenticar usuario
        if not user:														# Si no se encuentra el usuario
            messages.error(request, 'Usuario o contraseña incorrectos')
            return render(request, 'authentication/login.html')				# Redirigir a la vista de inicio de sesión
            
        if not user.email_verified:											# Si el email no está verificado
            messages.warning(request, 'Por favor verifica tu email para activar tu cuenta')
            return render(request, 'authentication/login.html')
            
        if user.two_factor_enabled:											# Si el usuario tiene 2FA habilitado
            # Guardar datos en sesión
            request.session['pending_user_id'] = user.id					# Guardar el ID del usuario en sesión				
            request.session['user_authenticated'] = True					# Marcar al usuario como autenticado
            request.session['manual_user'] = True	
            
            # Generar y enviar código 2FA
            code = TwoFactorService.generate_2fa_code(user)					# Generar código 2FA
            TwoFactorService.send_2fa_code(user, code)						# Enviar código 2FA por email
            
            # Usar HttpResponseRedirect con reverse
            return HttpResponseRedirect(reverse('verify_2fa'))				# Redirigir a la vista de verificación 2FA
            
        auth_login(request, user)
        if not remember:													# Si no se selecciona recordar sesión...
            request.session.set_expiry(0)									# Cerrar sesión al cerrar el navegador
        
        return redirect('user')												# Redirigir a la vista de perfil de usuario si la autenticación es exitosa
        
    return render(request, 'authentication/login.html')	

def register(request):
    """Vista de registro para nuevos usuarios que se registran manualmente"""
    if request.method == 'POST':											# Si se envía un formulario
        try:
            # Sanitizar entradas
            username = escape(request.POST.get('username', '').strip())		# Obtener nombre de usuario
            email = escape(request.POST.get('email', '').strip())			# Obtener email
            password = request.POST.get('password1')						# Obtener contraseña
            confirm_password = request.POST.get('password2')				# Obtener confirmación de contraseña
  
            # Validar datos (parseo de datos)
            try:
                PasswordService.validate_manual_registration(
                    username, 
                    email, 
                    password, 
                    confirm_password
                )
            except ValidationError as e:
                messages.error(request, str(e))
                return redirect('register')

			# Crear formulario de registro una vez validados los datos
            form = RegistrationForm(request.POST)
            if form.is_valid():
                user = AuthenticationService.register_user(
                    form.cleaned_data['username'],
                    form.cleaned_data['email'],
                    form.cleaned_data['password1']
                )
                token = TokenService.generate_verification_token(user)		# Generar token de verificación
                EmailService.send_verification_email(user, token)			# Enviar email de verificación
                messages.success(request, 'Revisa tu email para verificar tu cuenta')
                return redirect('login')
        except Exception as e:												# Capturar cualquier excepción
            messages.error(request, str(e))
            return redirect('register')
            
    return render(request, 'authentication/register.html')

def logout(request):
    """Vista de cierre de sesión"""
    auth_logout(request)
    return redirect('home')