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

urlpatterns = [
    path('', home, name='home'),
    path('login/', login, name='login'),
    path('register/', register, name='register'),
    path('user/', user, name='user'),
    path('logout/', logout, name='logout'),
    path('auth/42/', include('authentication.fortytwo_auth.urls', namespace='web_fortytwo_auth')),
    path('generate_qr/<str:username>/', generate_qr, name='generate_qr'),
    path('validate_qr/', validate_qr, name='validate_qr'),
    path('edit-profile/', edit_profile, name='edit_profile'),
    path('delete-account/', delete_account, name='delete_account'),
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
    path('verify-email/<str:uidb64>/<str:token>/', verify_email, name='verify_email'),
    path('verify-email-change/<str:uidb64>/<str:token>/', verify_email_change, name='verify_email_change'),
    path('enable-2fa/', enable_2fa, name='enable_2fa'),
    path('verify-2fa/', verify_2fa, name='verify_2fa'),
    path('disable-2fa/', disable_2fa, name='disable_2fa'),
    path('privacy-policy/', privacy_policy, name='privacy_policy'),
    path('gdpr-settings/', gdpr_settings, name='gdpr_settings'),
    path('export-data/', export_personal_data, name='export_data'),
    path('api/', include('authentication.api.urls', namespace='api')),
]