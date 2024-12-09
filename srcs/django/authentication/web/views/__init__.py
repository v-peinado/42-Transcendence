from .auth_views import login, register, logout, home  # Añadir home aquí
from .profile_views import edit_profile, delete_account, user
from .password_views import CustomPasswordResetView, CustomPasswordResetConfirmView
from .gdpr_views import gdpr_settings, privacy_policy, export_personal_data
from .verification_views import (
    verify_email, verify_email_change,
    enable_2fa, verify_2fa, disable_2fa,
    generate_qr, validate_qr
)

from django.urls import path, include

app_name = 'auth_api'

urlpatterns = [
    path('auth/', include(('authentication.api.urls.auth_urls', 'auth_api'), namespace='auth_api')),
    path('profile/', include('authentication.api.urls.profile_urls')),
    path('password/', include('authentication.api.urls.password_urls')),
    path('verify/', include('authentication.api.urls.verification_urls')),
]

__all__ = [
    'home',
    'login', 'register', 'logout',
    'edit_profile', 'delete_account', 'user',
    'CustomPasswordResetView', 'CustomPasswordResetConfirmView',
    'gdpr_settings', 'privacy_policy', 'export_personal_data',
    'verify_email', 'verify_email_change',
    'enable_2fa', 'verify_2fa', 'disable_2fa',
    'generate_qr', 'validate_qr'
]