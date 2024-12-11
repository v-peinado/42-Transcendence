from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from .views import (
    # auth_views
    home, login, register, logout,
    # gdpr_views
    gdpr_settings, export_personal_data, privacy_policy,
    # password_views
    CustomPasswordResetView, CustomPasswordResetConfirmView,
    # profile_views
    edit_profile, user, delete_account,
    # verification_views
    verify_email, verify_email_change,
    enable_2fa, verify_2fa, disable_2fa, 
    generate_qr, validate_qr,
)

# auth_views
auth_patterns = [
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),
    path('register/', register, name='register'),
    path('auth/42/', include('authentication.fortytwo_auth.urls', namespace='web_fortytwo_auth')),
]

# gdpr_views
gdpr_patterns = [
    path('gdpr-settings/', gdpr_settings, name='gdpr_settings'),
    path('export-data/', export_personal_data, name='export_data'),
    path('privacy-policy/', privacy_policy, name='privacy_policy'),
]

# profile_views
profile_patterns = [
    path('user/', user, name='user'),
    path('edit-profile/', edit_profile, name='edit_profile'),
    path('delete-account/', delete_account, name='delete_account'),
]

# password_views
password_patterns = [
    path('reset_password/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('reset_password/done/',  auth_views.PasswordResetDoneView.as_view(template_name='authentication/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(template_name='authentication/password_reset_confirm.html', success_url=reverse_lazy('login')), name='password_reset_confirm'),
    path('reset/complete/', auth_views.PasswordResetCompleteView.as_view(template_name='authentication/password_reset_complete.html'), name='password_reset_complete'),
]

# verification_views
verification_patterns = [
    path('verify-email/<str:uidb64>/<str:token>/', verify_email, name='verify_email'),
    path('verify-email-change/<str:uidb64>/<token>/', verify_email_change, name='verify_email_change'),
    path('enable-2fa/', enable_2fa, name='enable_2fa'),
    path('verify-2fa/', verify_2fa, name='verify_2fa'),
    path('disable-2fa/', disable_2fa, name='disable_2fa'),
    path('generate_qr/<str:username>/', generate_qr, name='generate_qr'),
    path('validate_qr/', validate_qr, name='validate_qr'),
]

# Unir todos los patrones
urlpatterns = [
    # Página principal
    path('', home, name='home'),
    
    # Incluir todos los grupos de URLs
    *auth_patterns,
    *profile_patterns,
    *password_patterns,
    *verification_patterns,
    *gdpr_patterns,
    
    # API endpoints
    path('api/', include('authentication.api.urls', namespace='api')),
]
