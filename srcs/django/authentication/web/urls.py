from django.urls import path, include, reverse_lazy
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.contrib.auth import views as auth_views
from .views import CustomPasswordResetView

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('user/', views.user, name='user'),
    path('logout/', views.custom_logout, name='logout'),
    path('auth/42/', include('authentication.fortytwo_auth.urls', namespace='web_fortytwo_auth')),
    path('generate_qr/<str:username>/', views.generate_qr, name='generate_qr'),
    path('validate_qr/', views.validate_qr, name='validate_qr'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('reset_password/', 
        CustomPasswordResetView.as_view(), 
        name='password_reset'),
    path('reset_password/done/', 
        auth_views.PasswordResetDoneView.as_view(
            template_name='authentication/password_reset_done.html'
        ), 
        name='password_reset_done'),
    path('reset/<uidb64>/<token>/', 
        views.CustomPasswordResetConfirmView.as_view(
            template_name='authentication/password_reset_confirm.html',
            success_url=reverse_lazy('login')
        ), 
        name='password_reset_confirm'),
    path('reset/complete/', 
        auth_views.PasswordResetCompleteView.as_view(
            template_name='authentication/password_reset_complete.html'
        ), 
        name='password_reset_complete'),
    path('verify-email/<str:uidb64>/<str:token>/', views.verify_email, name='verify_email'),
    path('enable-2fa/', views.enable_2fa, name='enable_2fa'),
    path('verify-2fa/', views.verify_2fa, name='verify_2fa'),
    path('disable-2fa/', views.disable_2fa, name='disable_2fa'),
]