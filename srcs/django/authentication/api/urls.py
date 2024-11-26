from django.urls import path, include
from . import views
from .views import (
    GenerateQRCodeView, 
    ValidateQRCodeView, 
    LoginView, 
    LogoutView,
    RegisterView,
    EditProfileView,
    DeleteAccountView,
    PasswordResetView, 
    PasswordResetConfirmView  
)

auth_patterns = [
    path('generate_qr/<str:username>/', GenerateQRCodeView.as_view(), name='generate_qr'),
    path('validate_qr/', ValidateQRCodeView.as_view(), name='validate_qr'),
    path('login/', LoginView.as_view(), name='api_login'),
    path('logout/', LogoutView.as_view(), name='api_logout'),
    path('register/', RegisterView.as_view(), name='api_register'),
    path('edit-profile/', EditProfileView.as_view(), name='api_edit_profile'),
    path('delete-account/', DeleteAccountView.as_view(), name='api_delete_account'),
    path('42/', include('authentication.fortytwo_auth.urls')),
    path('reset_password/', PasswordResetView.as_view(), name='api_password_reset'),
    path('reset_password/confirm/', PasswordResetConfirmView.as_view(), name='api_password_reset_confirm'),
    path('verify-email/<str:uidb64>/<str:token>/', views.verify_email, name='api_verify_email'),
    path('disable-2fa/', views.Disable2FAView.as_view(), name='api_disable_2fa'),
    path('verify-email-change/<str:uidb64>/<str:token>/', 
         views.VerifyEmailChangeView.as_view(), name='api_verify_email_change'),
]

# Patrón principal que incluye todas las rutas de autenticación
urlpatterns = [
    path('authentication/', include((auth_patterns, 'authentication'), namespace='auth_api')),
    path('validate-qr/', views.ValidateQRCodeAPIView.as_view(), name='api_validate_qr'),
    path('verify-2fa/', views.Verify2FAAPIView.as_view(), name='api_verify_2fa'),
    path('verify-2fa/', views.Verify2FAView.as_view(), name='api_verify_2fa'),
    path('gdpr/export-data/', views.ExportPersonalDataAPIView.as_view(), name='api_export_data'),
    path('gdpr/settings/', views.GDPRSettingsAPIView.as_view(), name='api_gdpr_settings'),
    path('gdpr/privacy-policy/', views.PrivacyPolicyAPIView.as_view(), name='api_privacy_policy'),
]

# Notas:
# Las rutas serán accesibles a través de http://localhost:8000/api/authentication/
# Rutas existentes:
# - /api/authentication/generate_qr/<str:username>/
# - /api/authentication/validate_qr/
# - /api/authentication/login/
# - /api/authentication/logout/
# - /api/authentication/register/
# - /api/authentication/edit-profile/
# - /api/authentication/delete-account/
# - /api/authentication/42/login/
# - /api/authentication/42/callback/
# - /api/authentication/reset_password/
# - /api/authentication/reset_password/confirm/

# Rutas GDPR:
# - /api/gdpr/export-data/
# - /api/gdpr/settings/
# - /api/gdpr/privacy-policy/

# Rutas de verificación:
# - /api/authentication/verify-email/<str:uidb64>/<str:token>/
# - /api/authentication/verify-email-change/<str:uidb64>/<str:token>/
# - /api/authentication/verify-2fa/
# - /api/authentication/disable-2fa/

# Rutas de verificación QR:
# - /api/validate-qr/
# - /api/verify-2fa/

# Todas las rutas tienen sus correspondientes nombres:
# 'api_login', 'api_logout', 'api_register', 'api_edit_profile',
# 'api_delete_account', 'api_fortytwo_login', 'api_fortytwo_callback',
# 'api_password_reset', 'api_password_reset_confirm', 'api_verify_email',
# 'api_verify_email_change', 'api_disable_2fa', 'api_validate_qr',
# 'api_verify_2fa', 'api_export_data', 'api_gdpr_settings',
# 'api_privacy_policy'