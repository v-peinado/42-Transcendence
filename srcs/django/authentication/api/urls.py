from django.urls import path
from ninja import NinjaAPI
from authentication.api.controllers import router as auth_router
from authentication.fortytwo_auth.views import FortyTwoLoginAPIView, FortyTwoCallbackAPIView

from .views import (
    # auth_views
    LoginAPIView, LogoutAPIView, RegisterAPIView,
    # gdpr_views
    GDPRSettingsAPIView, ExportPersonalDataAPIView, PrivacyPolicyAPIView,
    # pass_reset_views
    PasswordResetAPIView, PasswordResetConfirmAPIView,
    # profile_views
    EditProfileAPIView, UserProfileAPIView, DeleteAccountAPIView,
    # verify_email_views
    VerifyEmailAPIView, VerifyEmailChangeAPIView,
	# qr_views
    GenerateQRAPIView, ValidateQRAPIView,
    # two_factor_views
    Enable2FAView, Verify2FAAPIView, Disable2FAView
)

# Configuración Django Ninja
api = NinjaAPI(
    title='Authentication API',
    version='2.0.0',
    description='API para autenticación y gestión de usuarios',
    urls_namespace='auth_api',
    docs_url="/docs"
)

# Agregar router de autenticación
api.add_router("/auth/", auth_router)

# auth_views
auth_patterns = [
    path('login/', LoginAPIView.as_view(), name='api_login'),
    path('logout/', LogoutAPIView.as_view(), name='api_logout'),
    path('register/', RegisterAPIView.as_view(), name='api_register'),
]

# qr_patterns
qr_patterns = [
    path('generate-qr/<str:username>/', GenerateQRAPIView.as_view(), name='api_generate_qr'),
    path('validate-qr/', ValidateQRAPIView.as_view(), name='api_validate_qr'),
]

# gdpr_views
gdpr_patterns = [
    path('gdpr/settings/', GDPRSettingsAPIView.as_view(), name='api_gdpr_settings'),
    path('gdpr/export-data/', ExportPersonalDataAPIView.as_view(), name='api_export_data'),
    path('gdpr/privacy-policy/', PrivacyPolicyAPIView.as_view(), name='api_privacy_policy'),
]

# profile_views
profile_patterns = [
    path('profile/', EditProfileAPIView.as_view(), name='api_profile'),
	path('profile/user/', UserProfileAPIView.as_view(), name='api_user_profile'),
	path('profile/delete-account/', DeleteAccountAPIView.as_view(), name='api_delete_account'),
]

# pass_reset_views
password_patterns = [
    path('password/reset/', PasswordResetAPIView.as_view(), name='api_password_reset'),
    path('password/reset/confirm/', PasswordResetConfirmAPIView.as_view(), name='api_password_reset_confirm'),
]

# verify_email_views
verification_patterns = [
    path('verify-email/<str:uidb64>/<str:token>/', VerifyEmailAPIView.as_view(), name='api_verify_email'),
    path('verify-email-change/<str:uidb64>/<str:token>/', VerifyEmailChangeAPIView.as_view(), name='api_verify_email_change'),
]

# two_factor_views
two_factor_patterns = [
    path('enable-2fa/', Enable2FAView.as_view(), name='api_enable_2fa'),
    path('verify-2fa/', Verify2FAAPIView.as_view(), name='api_verify_2fa'),
    path('disable-2fa/', Disable2FAView.as_view(), name='api_disable_2fa'),
]

# URLs de la API
fourtytwo_patterns = [
    path('api/login/', FortyTwoLoginAPIView.as_view(), name='api_ft_login'),
    path('api/callback/', FortyTwoCallbackAPIView.as_view(), name='api_ft_callback'),
]

urlpatterns = [
    *auth_patterns,
	*qr_patterns,
    *gdpr_patterns, 
    *profile_patterns,
    *password_patterns,
    *verification_patterns,
    *two_factor_patterns,
	*fourtytwo_patterns,
    
    path('ninja/', api.urls),
]

"""
URLs ABSOLUTAS API (Base: http://localhost:8000):

 AUTENTICACIÓN (URLs Django):
   * http://localhost:8000/api/login/
   * http://localhost:8000/api/logout/
   * http://localhost:8000/api/register/

 GDPR Y PRIVACIDAD (URLs Django):
   * http://localhost:8000/api/gdpr/settings/
   * http://localhost:8000/api/gdpr/export-data/
   * http://localhost:8000/api/gdpr/privacy-policy/

 PERFIL (URLs Django):
   * http://localhost:8000/api/profile/
   * http://localhost:8000/api/profile/user/
   * http://localhost:8000/api/profile/delete-account/

 CONTRASEÑA (URLs Django):
   * http://localhost:8000/api/password/reset/
   * http://localhost:8000/api/password/reset/confirm/

 EMAIL (URLs Django):
   * http://localhost:8000/api/verify-email/<str:uidb64>/<str:token>/
   * http://localhost:8000/api/verify-email-change/<str:uidb64>/<str:token>/

 QR Y 2FA (URLs Django):
   * http://localhost:8000/api/generate-qr/<str:username>/
   * http://localhost:8000/api/validate-qr/
   * http://localhost:8000/api/enable-2fa/
   * http://localhost:8000/api/verify-2fa/
   * http://localhost:8000/api/disable-2fa/

 DJANGO NINJA (Nueva API):
   * http://localhost:8000/api/ninja/docs         -> Documentación Swagger/OpenAPI
   * http://localhost:8000/api/ninja/openapi.json -> Especificación OpenAPI
"""