from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, update_session_auth_hash
from django.contrib import messages
from ...utils.validation import validate_printable_chars
from django.core.exceptions import ValidationError
from ...services.auth_service import AuthenticationService
from ...services.email_service import EmailService
from ...services.token_service import TokenService
from ...services.password_service import PasswordService
from ..forms.auth_forms import RegistrationForm
from ...services.two_factor_service import TwoFactorService
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.hashers import check_password  # Añadir esta línea

# Importaciones adicionales necesarias
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from ...models import CustomUser, PreviousPassword
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

def home(request):
    """Vista principal"""
    return render(request, 'authentication/home.html')

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username').strip().lower()
        password = request.POST.get('password')
        remember = request.POST.get('remember', None)

        user = authenticate(request, username=username, password=password)
        if not user:
            messages.error(request, 'Usuario o contraseña incorrectos')
            return render(request, 'authentication/login.html')
            
        if not user.email_verified:
            messages.warning(request, 'Por favor verifica tu email para activar tu cuenta')
            return render(request, 'authentication/login.html')
            
        if user.two_factor_enabled:
            # Guardar datos en sesión
            request.session['pending_user_id'] = user.id
            request.session['user_authenticated'] = True
            request.session['manual_user'] = True
            
            # Generar y enviar código 2FA
            code = TwoFactorService.generate_2fa_code(user)
            TwoFactorService.send_2fa_code(user, code)
            
            # Usar HttpResponseRedirect con reverse
            return HttpResponseRedirect(reverse('verify_2fa'))
            
        auth_login(request, user)
        if not remember:
            request.session.set_expiry(0)
        
        return redirect('user')
        
    return render(request, 'authentication/login.html')

def register(request):
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password1')
            confirm_password = request.POST.get('password2')
            
            # Verificar si ya existe el usuario
            if CustomUser.objects.filter(username=username.lower()).exists():
                messages.error(request, "Este nombre de usuario ya está en uso")
                return redirect('register')
                
            # Verificar si ya existe el email
            if CustomUser.objects.filter(email=email.lower()).exists():
                messages.error(request, "Este email ya está registrado")
                return redirect('register')
                
            # Validar datos usando PasswordService
            try:
                PasswordService.validate_registration_password(
                    username, 
                    email, 
                    password, 
                    confirm_password
                )
            except ValidationError as e:
                messages.error(request, str(e))
                return redirect('register')

            form = RegistrationForm(request.POST)
            if form.is_valid():
                user = AuthenticationService.register_user(
                    form.cleaned_data['username'],
                    form.cleaned_data['email'],
                    form.cleaned_data['password1']
                )
                token = TokenService.generate_verification_token(user)
                EmailService.send_verification_email(user, token)
                messages.success(request, 'Revisa tu email para verificar tu cuenta')
                return redirect('login')
        except Exception as e:
            messages.error(request, str(e))
            return redirect('register')
            
    return render(request, 'authentication/register.html')

def logout(request):
    auth_logout(request)
    return redirect('home')

@staticmethod
def authenticate_user(username, password):
    """Autenticación de usuario"""
    try:
        user = authenticate(username=username, password=password)
        if not user:
            raise ValidationError("Credenciales inválidas")
        return user
    except Exception as e:
        raise ValidationError(f"Error en autenticación: {str(e)}")

@method_decorator(csrf_exempt, name='dispatch')
class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            username = request.data.get('username')
            password = request.data.get('password')
            user = authenticate(username=username, password=password)
            if user:
                auth_login(request, user)
                return Response({'message': 'Login successful'}, status=status.HTTP_200_OK)
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)