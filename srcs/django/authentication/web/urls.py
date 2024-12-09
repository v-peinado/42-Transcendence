from django.urls import path, include, reverse_lazy
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    login, register, logout, home,
    edit_profile, delete_account, user,
    CustomPasswordResetView, CustomPasswordResetConfirmView,
    gdpr_settings, privacy_policy, export_personal_data,
    verify_email, verify_email_change,
    enable_2fa, verify_2fa, disable_2fa,
    generate_qr, validate_qr
)
from django.contrib.auth import views as auth_views

# authentication/urls/auth_urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from ..web.views import auth_views, verification_views, profile_views

# Autenticación básica:
# - register: Registro de usuario
# - login: Inicio de sesión
# - logout: Cierre de sesión
# - auth/42: Autenticación con 42
auth_patterns = [
    path('register/', auth_views.register, name='register'),
    path('login/', auth_views.login, name='login'),
    path('logout/', auth_views.logout, name='logout'),
    path('auth/42/', include('authentication.fortytwo_auth.urls', namespace='web_fortytwo_auth')),
]

# Verificación:
# - verify_email: Verifica la dirección de correo electrónico del usuario
# - generate_qr: Genera un código QR para la autenticación:
# - validate_qr: Valida el código QR generado
verification_patterns = [
    path('verify-email/<str:uidb64>/<str:token>/', verification_views.verify_email, name='verify_email'),
    path('generate_qr/<str:username>/', verification_views.generate_qr, name='generate_qr'),
    path('validate_qr/', verification_views.validate_qr, name='validate_qr'),
]

# Gestión de perfil:
# - user: Muestra la información del usuario
# - edit_profile: Permite al usuario editar su perfil
# - delete_account: Permite al usuario eliminar su cuenta
profile_patterns = [
    path('user/', profile_views.user, name='user'),
    path('edit-profile/', profile_views.edit_profile, name='edit_profile'),
    path('delete-account/', profile_views.delete_account, name='delete_account'),
]

# Gestión de contraseña:
# - reset_password: Inicia el proceso de restablecimiento de contraseña
# - reset_password/done: Muestra un mensaje de éxito después de enviar el correo electrónico
# - reset/<uidb64>/<token>: Verifica el token y permite al usuario cambiar la contraseña
# - reset/complete: Muestra un mensaje de éxito después de cambiar la contraseña
password_patterns = [
    path('reset_password/', 
        CustomPasswordResetView.as_view(), 
        name='password_reset'),
    path('reset_password/done/', 
        auth_views.PasswordResetDoneView.as_view(
            template_name='authentication/password_reset_done.html'
        ), 
        name='password_reset_done'),
    path('reset/<uidb64>/<token>/', 
        CustomPasswordResetConfirmView.as_view(
            template_name='authentication/password_reset_confirm.html',
            success_url=reverse_lazy('login')
        ), 
        name='password_reset_confirm'),
    path('reset/complete/', 
        auth_views.PasswordResetCompleteView.as_view(
            template_name='authentication/password_reset_complete.html'
        ), 
        name='password_reset_complete'),
]

# Patrones de URL se dividen en cuatro categorías:
# - Autenticación: Registro, inicio de sesión, cierre de sesión, autenticación con 42
# - Verificación: Verificación de correo electrónico, generación y validación de códigos QR
# - Perfil: Información del usuario, edición de perfil, eliminación de cuenta
# - Contraseña: Restablecimiento de contraseña, verificación de token, cambio de contraseña
urlpatterns = [
    path('', include((auth_patterns, 'auth'))),
    path('verification/', include((verification_patterns, 'verification'))),
    path('profile/', include((profile_patterns, 'profile'))),
    path('password/', include((password_patterns, 'password'))),
]