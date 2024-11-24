from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from authentication.models import CustomUser
import qrcode
import io
import json
import re 
from django.views.decorators.csrf import csrf_exempt  
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from ..models import CustomUser 
from ..serializers.user_serializers import UserSerializer
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.views import PasswordResetView
from django.db.models import Q
from django.urls import reverse_lazy, reverse
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.conf import settings
from .utils import generate_jwt_token, decode_jwt_token
from django.core.cache import cache
import pyotp
from .utils import generate_2fa_code, send_2fa_code, verify_2fa_code
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.views import PasswordResetConfirmView
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings

# Vista principal
def home(request):
    return render(request, 'authentication/home.html')

# Función de login para usuarios manuales
def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

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
            request.session['manual_user'] = True  # Añadir flag para usuarios manuales
            
            # Generar y enviar código 2FA
            code = generate_2fa_code(user)
            send_2fa_code(user, code)
            
            # Importante: redireccionar en lugar de renderizar
            return redirect('verify_2fa')
            
        auth_login(request, user)
        return redirect('user')
        
    return render(request, 'authentication/login.html')

# Vista de registro
def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password1')
        confirm_password = request.POST.get('password2')

        # Validar caracteres no permitidos en username
        if not validate_printable_chars(username):
            messages.error(request, "El nombre de usuario no puede contener espacios ni caracteres especiales")
            return redirect('register')

        # Validar caracteres no permitidos en email
        email_local_part = email.split('@')[0] if '@' in email else email
        if not validate_printable_chars(email_local_part):
            messages.error(request, "El email no puede contener espacios ni caracteres especiales")
            return redirect('register')

        # Validar caracteres no permitidos en password
        if not validate_printable_chars(password):
            messages.error(request, "La contraseña no puede contener espacios ni caracteres especiales")
            return redirect('register')

        # Validar username y email de 42
        if username.startswith('42.'):
            messages.error(request, "El prefijo '42.' está reservado para usuarios de 42")
            return redirect('register')

        if re.match(r'.*@student\.42.*\.com$', email.lower()):
            messages.error(request, "Los correos con dominio @student.42*.com están reservados para usuarios de 42")
            return redirect('register')

        # Validar contraseña segura
        try:
            validate_password(password)
        except ValidationError as e:
            messages.error(request, e.messages[0])
            return redirect('register')

        if password != confirm_password:
            messages.error(request, "Las contraseñas no coinciden")
            return redirect('register')

        try:
            # Crear usuario pero no activarlo
            user = CustomUser.objects.create_user(
                username=username.lower(),
                email=email.lower(),
                password=password,
                is_fortytwo_user=False,
                is_active=False  # Usuario inactivo hasta verificar email
            )
            
            # Generar token JWT
            token = generate_jwt_token(user)
            user.email_verification_token = token
            user.save()
            
            # Enviar solo el email de verificación
            subject = 'Verifica tu cuenta de PongOrama'
            plain_message = f"""
            Hola {user.username},
            
            Gracias por registrarte en PongOrama. Para verificar tu cuenta, haz clic en el siguiente enlace:
            {settings.SITE_URL}/verify-email/{urlsafe_base64_encode(force_bytes(user.pk))}/{token}/
            
            Si no has sido tú quien ha creado esta cuenta, por favor contacta con nuestro soporte.
            
            Saludos,
            El equipo de PongOrama
            """
            html_message = render_to_string('authentication/email_verification.html', {
                'user': user,
                'domain': settings.SITE_URL,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': token,
                'protocol': 'https'
            })
            
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
                html_message=html_message
            )
            
            messages.success(request, "Te hemos enviado un email para verificar tu cuenta")
            return redirect('login')
            
        except Exception as e:
            messages.error(request, str(e))
            return redirect('register')
            
    return render(request, 'authentication/register.html')

# Vista para mostrar todos los usuarios
@login_required
def user(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    context = {
        'user': request.user,
        'show_qr': True  # Para controlar la visualización del QR
    }
    return render(request, 'authentication/user.html', context)

# Vista personalizada de logout
@login_required
def custom_logout(request):
    auth_logout(request)
    return redirect('home')

# Función para generar QR
@login_required
def generate_qr(request, username):
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

# Función para validar QR
@csrf_exempt  # Mantener csrf_exempt
def validate_qr(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')  # Cambiar qr_data por username
            
            if not username:
                return JsonResponse({'success': False, 'error': 'Código QR inválido'})
                
            user = CustomUser.objects.filter(username=username).first()
            
            if user:
                auth_login(request, user)
                return JsonResponse({
                    'success': True,
                    'redirect_url': '/user/'  # Añadir URL de redirección
                })
            else:
                return JsonResponse({'success': False, 'error': 'Usuario no encontrado'})
                
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Datos inválidos'})
            
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

# Vistas de API
class UserList(generics.ListCreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password1')  # Actualizado para coincidir
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return Response({"message": "Login successful"}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    def post(self, request):
        auth_logout(request)
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        user = request.user
        
        # Manejar la restauración de la imagen de 42
        if user.is_fortytwo_user and 'restore_42_image' in request.POST:
            user.profile_image = None
            user.save()
            messages.success(request, 'Imagen de perfil restaurada a la imagen de 42')
            return redirect('user')
            
        # Manejar cambio de imagen normal
        if 'profile_image' in request.FILES:
            user.profile_image = request.FILES['profile_image']
            
        # Para usuarios normales, permitir cambios excepto username
        if not user.is_fortytwo_user:
            email = request.POST.get('email')
            
            # Validar que el email no sea de 42
            if email and email != user.email:
                if re.match(r'.*@student\.42.*\.com$', email.lower()):
                    messages.error(request, 'Los correos con dominio @student.42*.com están reservados para usuarios de 42')
                    return redirect('edit_profile')
                    
                if CustomUser.objects.exclude(id=user.id).filter(email=email).exists():
                    messages.error(request, 'Este email ya está en uso')
                    return redirect('edit_profile')
                    
                user.email = email

            # Validar y actualizar contraseña si se proporcionó
            current_password = request.POST.get('current_password')
            new_password1 = request.POST.get('new_password1')
            new_password2 = request.POST.get('new_password2')
            
            if current_password and new_password1 and new_password2:
                if not user.check_password(current_password):
                    messages.error(request, 'La contraseña actual es incorrecta')
                    return redirect('edit_profile')
                if new_password1 != new_password2:
                    messages.error(request, 'Las nuevas contraseñas no coinciden')
                    return redirect('edit_profile')
                
                # Aplicar validación de contraseña fuerte
                try:
                    validate_password(new_password1, user)
                except ValidationError as e:
                    for error in e.messages:
                        messages.error(request, error)
                    return redirect('edit_profile')
                    
                # Si pasa la validación, cambiar contraseña
                user.set_password(new_password1)
                update_session_auth_hash(request, user)
                
                # Enviar email solo si el cambio es desde el perfil
                if not request.session.get('password_reset_flow'):
                    subject = 'Tu contraseña ha sido cambiada'
                    message = render_to_string('authentication/password_changed_email.html', {
                        'user': user,
                        'reset': False
                    })
                    
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=False
                    )

        try:
            user.save()
            messages.success(request, 'Perfil actualizado correctamente')
            return redirect('user')
        except ValidationError as e:
            # Capturar y mostrar errores de validación del modelo
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f'{error}')
            return redirect('edit_profile')
            
    return render(request, 'authentication/edit_profile.html')

@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        password = request.POST.get('confirm_password')

        # Si es un usuario de 42, permitir la eliminación sin contraseña
        if user.is_fortytwo_user:
            user.delete()
            auth_logout(request)
            messages.success(request, 'Tu cuenta ha sido eliminada correctamente')
            return redirect('home')
        # Para usuarios normales, verificar la contraseña
        else:
            if user.check_password(password):
                user.delete()
                auth_logout(request)
                messages.success(request, 'Tu cuenta ha sido eliminada correctamente')
                return redirect('home')
            else:
                messages.error(request, 'Contraseña incorrecta')
                return redirect('edit_profile')

    return redirect('edit_profile')

def validate_printable_chars(text):
    if not text:
        return False
    # Comprobar espacios y tabulaciones
    if any(char.isspace() for char in text):
        return False
    # Validar que todos los caracteres sean imprimibles
    return all(char.isprintable() and not char.isspace() for char in text)

class CustomPasswordResetView(PasswordResetView):
    success_url = reverse_lazy('password_reset_done')
    email_template_name = 'authentication/password_reset_email.html'
    template_name = 'authentication/password_reset.html'

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        
        # Verificar si es un email de 42
        if re.match(r'.*@student\.42.*\.com$', email.lower()):
            messages.error(
                self.request, 
                "Los usuarios de 42 deben iniciar sesión a través del botón de login de 42."
            )
            return self.form_invalid(form)
        
        # Verificar si existe el usuario
        users = CustomUser.objects.filter(
            email__iexact=email,
            is_active=True,
            is_fortytwo_user=False
        )
        
        if not list(users):
            messages.error(self.request, "No existe una cuenta con este correo electrónico.")
            return self.form_invalid(form)
            
        if users.first().is_fortytwo_user:
            messages.error(self.request, "Los usuarios de 42 no pueden usar esta función.")
            return self.form_invalid(form)

        # Solo enviar el email de recuperación, no el de notificación
        return super().form_valid(form)

    def get_users(self, email):
        active_users = CustomUser.objects.filter(
            email__iexact=email, 
            is_active=True,
            is_fortytwo_user=False
        )
        return (u for u in active_users if u.has_usable_password())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['protocol'] = 'https'
        return context

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    def form_valid(self, form):
        self.request.session['password_reset_flow'] = True
        response = super().form_valid(form)
        user = form.user
        
        # Enviar email
        subject = 'Tu contraseña ha sido cambiada'
        plain_message = f"""
        Hola {user.username},
        
        Tu contraseña de PongOrama ha sido cambiada exitosamente mediante el proceso de recuperación de contraseña.
        
        Si no has sido tú quien ha realizado este cambio, por favor contacta inmediatamente con nuestro equipo de soporte.
        
        Saludos,
        El equipo de PongOrama
        """
        html_message = render_to_string('authentication/password_changed_email.html', {
            'user': user,
            'reset': True
        })
        
        send_mail(
            subject,
            plain_message,  # Mensaje en texto plano
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
            html_message=html_message  # Mensaje HTML
        )
        
        # Limpiar la marca del flujo
        if 'password_reset_flow' in self.request.session:
            del self.request.session['password_reset_flow']
            
        messages.success(self.request, "Tu contraseña ha sido actualizada correctamente")
        return response

def verify_email(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = CustomUser.objects.get(pk=uid)
        payload = decode_jwt_token(token)
        
        if user and payload and payload['user_id'] == user.id:
            user.email_verified = True
            user.is_active = True
            user.email_verification_token = None
            user.save()
            
            # Enviar solo un email de bienvenida
            subject = '¡Bienvenido a PongOrama!'
            plain_message = f"""
            Hola {user.username},
            
            ¡Bienvenido a PongOrama! Tu cuenta ha sido verificada exitosamente.
            
            Saludos,
            El equipo de PongOrama
            """
            html_message = render_to_string('authentication/welcome_email.html', {
                'user': user
            })
            
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
                html_message=html_message
            )
            
            messages.success(request, "Tu cuenta ha sido verificada correctamente hora puedes iniciar sesión")
            return redirect('login')
        else:
            messages.error(request, "El enlace de verificación no es válido")
            return redirect('login')
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        messages.error(request, "El enlace de verificación no es válido o ha expirado")
        return redirect('login')

@login_required
def enable_2fa(request):
    if request.method == 'POST':
        user = request.user
        action = request.POST.get('action')
        
        if action == 'enable':
            user.two_factor_enabled = True
            if not user.two_factor_secret:
                user.two_factor_secret = pyotp.random_base32()
            message = '2FA activado correctamente'
        else:
            user.two_factor_enabled = False
            user.two_factor_secret = None
            message = '2FA desactivado correctamente'
            
        user.save()
        messages.success(request, message)
        return redirect('user')
        
    return render(request, 'authentication/enable_2fa.html')

def verify_2fa(request):
    # Verificar autenticación previa
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
        # Limpiar sesión
        for key in ['pending_user_id', 'user_authenticated', 'fortytwo_user', 'manual_user']:
            if key in request.session:
                del request.session[key]
        return redirect('login')

    if request.method == 'POST':
        code = request.POST.get('code')
        
        if verify_2fa_code(user, code):
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
    if request.method == 'POST':
        user = request.user
        user.two_factor_enabled = False
        user.two_factor_secret = None
        user.save()
        messages.success(request, '2FA desactivado correctamente')
        return redirect('user')
    return HttpResponseNotAllowed(['POST'])