from django.urls import path, include
from .views import (
    # auth_views
    LoginAPIView, LogoutAPIView, RegisterAPIView,
    # gdpr_views
    GDPRSettingsAPIView, ExportPersonalDataAPIView, PrivacyPolicyAPIView, DeleteAccountAPIView,
    # pass_reset_views
    PasswordResetAPIView, PasswordResetConfirmAPIView, PasswordChangeAPIView,
    # profile_views
    ProfileAPIView, ProfileImageAPIView, DeleteAccountView,
    # verify_email_views
    VerifyEmailAPIView, VerifyEmailChangeAPIView,
	# qr_views
    GenerateQRAPIView, ValidateQRAPIView,
    # two_factor_views
    Enable2FAView, Verify2FAAPIView, Disable2FAView
)

# auth_views
auth_patterns = [
    path('login/', LoginAPIView.as_view(), name='api_login'),
    path('logout/', LogoutAPIView.as_view(), name='api_logout'),
    path('register/', RegisterAPIView.as_view(), name='api_register'),
]

# qr_patterns
qr_patterns = [
    path('generate-qr/<str:username>/', GenerateQRAPIView, name='api_generate_qr'),
    path('validate-qr/', ValidateQRAPIView, name='api_validate_qr'),
]

# gdpr_views
gdpr_patterns = [
    path('gdpr/settings/', GDPRSettingsAPIView.as_view(), name='api_gdpr_settings'),
    path('gdpr/export-data/', ExportPersonalDataAPIView.as_view(), name='api_export_data'),
    path('gdpr/privacy-policy/', PrivacyPolicyAPIView.as_view(), name='api_privacy_policy'),
    path('gdpr/delete-account/', DeleteAccountAPIView.as_view(), name='api_delete_account'),
]

# profile_views
profile_patterns = [
    path('profile/', ProfileAPIView.as_view(), name='api_profile'),
    path('profile/image/', ProfileImageAPIView.as_view(), name='api_profile_image'),
    path('profile/delete/', DeleteAccountView.as_view(), name='api_delete_account'),
]

# pass_reset_views
password_patterns = [
    path('password/reset/', PasswordResetAPIView.as_view(), name='api_password_reset'),
    path('password/reset/confirm/', PasswordResetConfirmAPIView.as_view(), name='api_password_reset_confirm'),
    path('password/change/', PasswordChangeAPIView.as_view(), name='api_password_change'),
]

# verify_email_views
verification_patterns = [
    path('verify-email/<str:uidb64>/<str:token>/', VerifyEmailAPIView.as_view(), name='api_verify_email'),
    path('verify-email-change/<str:uidb64>/<str:token>/', VerifyEmailChangeAPIView.as_view(), name='api_verify_email_change'),
]

# two_factor_views
two_factor_patterns = [
    path('enable-2fa/', Enable2FAView, name='api_enable_2fa'),
    path('verify-2fa/', Verify2FAAPIView, name='api_verify_2fa'),
    path('disable-2fa/', Disable2FAView, name='api_disable_2fa'),
]

urlpatterns = [
    *auth_patterns,
	*qr_patterns,
    *gdpr_patterns, 
    *profile_patterns,
    *password_patterns,
    *verification_patterns,
    *two_factor_patterns
]
