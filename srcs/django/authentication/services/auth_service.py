from django.core.exceptions import ValidationError
from authentication.models import CustomUser
from .mail_service import MailSendingService
from .token_service import TokenService
from .password_service import PasswordService
from .two_factor_service import TwoFactorService
from authentication.forms.auth_forms import RegistrationForm
from django.contrib.auth import authenticate, login as auth_login
from django.utils.html import escape
from authentication.models import PreviousPassword

class AuthenticationService:
    @staticmethod
    def register_user(username, email, password):
        """Registro básico de usuario"""
        user = CustomUser.objects.create_user(
            username=username.lower(),
            email=email.lower(),
            password=password,
            is_active=False
        )
        return user

    @staticmethod
    def login_user(request, username, password, remember=False):
        """Gestiona el proceso de login"""
        user = authenticate(request, username=username.strip().lower(), password=password)
        
        if not user:
            raise ValidationError('Usuario o contraseña incorrectos')
            
        if not user.email_verified:
            raise ValidationError('Por favor verifica tu email para activar tu cuenta')
            
        if user.two_factor_enabled:
            request.session.update({
                'pending_user_id': user.id,
                'user_authenticated': True,
                'manual_user': True
            })
            
            code = TwoFactorService.generate_2fa_code(user)
            TwoFactorService.send_2fa_code(user, code)
            return 'verify_2fa'
            
        auth_login(request, user)
        if not remember:
            request.session.set_expiry(0)
            
        return 'user'

    @staticmethod
    def handle_registration(form_data):
        """Gestiona el proceso de registro"""
        username = escape(form_data.get('username', '').strip())
        email = escape(form_data.get('email', '').strip())
        password = form_data.get('password1')
        confirm_password = form_data.get('password2')

        # Validar datos
        PasswordService.validate_manual_registration(
            username, 
            email, 
            password, 
            confirm_password
        )

        form = RegistrationForm(form_data)
        if form.is_valid():
            # Crear usuario
            user = AuthenticationService.register_user(
                form.cleaned_data['username'],
                form.cleaned_data['email'],
                form.cleaned_data['password1']
            )
            
            # Guardar contraseña inicial en historial
            PreviousPassword.objects.create(user=user, password=user.password)
            
            # Generar y enviar token de verificación
            token = TokenService.generate_email_verification_token(user)
            MailSendingService.send_verification_email(user, token)
            return True
            
        return False