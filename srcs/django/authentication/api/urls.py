from django.urls import path
from ninja import NinjaAPI
from authentication.api.controllers import router as auth_router
from authentication.fortytwo_auth.views import (
    FortyTwoLoginAPIView,
    FortyTwoCallbackAPIView,
    FortyTwoVerify2FAView,
)

from .views import (
    # auth_views
    LoginAPIView,
    LogoutAPIView,
    RegisterAPIView,
    # gdpr_views
    GDPRSettingsAPIView,
    ExportPersonalDataAPIView,
    PrivacyPolicyAPIView,
    # pass_reset_views
    PasswordResetAPIView,
    PasswordResetConfirmAPIView,
    # profile_views
    EditProfileAPIView,
    UserProfileAPIView,
    DeleteAccountAPIView,
    # verify_email_views
    VerifyEmailAPIView,
    VerifyEmailChangeAPIView,
    # qr_views
    GenerateQRAPIView,
    ValidateQRAPIView,
    # two_factor_views
    Enable2FAView,
    Verify2FAAPIView,
    Disable2FAView,
)

# Django Ninja Configuration
api = NinjaAPI(
    title="Authentication API",
    version="2.0.0",
    description="API para autenticación y gestión de usuarios",
    urls_namespace="auth_api",
    docs_url="/docs",
)

# Add authentication router
api.add_router("/auth/", auth_router)

# Authentication views
auth_patterns = [
    path("login/", LoginAPIView.as_view(), name="api_login"),
    path("logout/", LogoutAPIView.as_view(), name="api_logout"),
    path("register/", RegisterAPIView.as_view(), name="api_register"),
]

# QR patterns
qr_patterns = [
    path(
        "generate-qr/<str:username>/",
        GenerateQRAPIView.as_view(),
        name="api_generate_qr",
    ),
    path("validate-qr/", ValidateQRAPIView.as_view(), name="api_validate_qr"),
]

# GDPR views
gdpr_patterns = [
    path("gdpr/settings/", GDPRSettingsAPIView.as_view(), name="api_gdpr_settings"),
    path(
        "gdpr/export-data/download/",
        ExportPersonalDataAPIView.as_view(),
        {"download": True},
        name="api_export_data_download"
    ),
    path(
        "gdpr/privacy-policy/",
        PrivacyPolicyAPIView.as_view(),
        name="api_privacy_policy",
    ),
]

# Profile views
profile_patterns = [
    path("profile/", EditProfileAPIView.as_view(), name="api_profile"),
    path("profile/user/", UserProfileAPIView.as_view(), name="api_user_profile"),
    path(
        "profile/delete-account/",
        DeleteAccountAPIView.as_view(),
        name="api_delete_account",
    ),
]

# Password reset views
password_patterns = [
    path("password/reset/", PasswordResetAPIView.as_view(), name="api_password_reset"),
    path(
        "password/reset/confirm/",
        PasswordResetConfirmAPIView.as_view(),
        name="api_password_reset_confirm",
    ),
]

# Email verification views
verification_patterns = [
    path(
        "verify-email/<str:uidb64>/<str:token>/",
        VerifyEmailAPIView.as_view(),
        name="api_verify_email",
    ),
    path(
        "verify-email-change/<str:uidb64>/<str:token>/",
        VerifyEmailChangeAPIView.as_view(),
        name="api_verify_email_change",
    ),
]

# Two-factor authentication views
two_factor_patterns = [
    path("enable-2fa/", Enable2FAView.as_view(), name="api_enable_2fa"),
    path("verify-2fa/", Verify2FAAPIView.as_view(), name="api_verify_2fa"),
    path("disable-2fa/", Disable2FAView.as_view(), name="api_disable_2fa"),
]

# API URLs
fourtytwo_patterns = [
    path(
        "authentication/42/api/login/",
        FortyTwoLoginAPIView.as_view(),
        name="api_ft_login",
    ),
    path(
        "authentication/42/api/callback/",
        FortyTwoCallbackAPIView.as_view(),
        name="api_ft_callback",
    ),
    path(
        "auth/42/verify-2fa/",
        FortyTwoVerify2FAView.as_view(),
        name="fortytwo_verify_2fa",
    ),  # Cambiar ruta
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
    path("ninja/", api.urls),
]

"""
ABSOLUTE API URLs (Base: http://localhost:8000):

 AUTHENTICATION (Django URLs):
   * http://localhost:8000/api/login/
   * http://localhost:8000/api/logout/
   * http://localhost:8000/api/register/

 GDPR AND PRIVACY (Django URLs):
   * http://localhost:8000/api/gdpr/settings/
   * http://localhost:8000/api/gdpr/export-data/
   * http://localhost:8000/api/gdpr/privacy-policy/

 PROFILE (Django URLs):
   * http://localhost:8000/api/profile/
   * http://localhost:8000/api/profile/user/
   * http://localhost:8000/api/profile/delete-account/

 PASSWORD (Django URLs):
   * http://localhost:8000/api/password/reset/
   * http://localhost:8000/api/password/reset/confirm/

 EMAIL (Django URLs):
   * http://localhost:8000/api/verify-email/<str:uidb64>/<str:token>/
   * http://localhost:8000/api/verify-email-change/<str:uidb64>/<str:token>/

 QR AND 2FA (Django URLs):
   * http://localhost:8000/api/generate-qr/<str:username>/
   * http://localhost:8000/api/validate-qr/
   * http://localhost:8000/api/enable-2fa/
   * http://localhost:8000/api/verify-2fa/
   * http://localhost:8000/api/disable-2fa/

 DJANGO NINJA (New API):
   * http://localhost:8000/api/ninja/docs         -> Swagger/OpenAPI Documentation
   * http://localhost:8000/api/ninja/openapi.json -> OpenAPI Specification
"""
