from django.urls import path, include
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
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('reset_password/', 
        CustomPasswordResetView.as_view(), 
        name='password_reset'),
    path('reset_password/done/', 
        auth_views.PasswordResetDoneView.as_view(
            template_name='authentication/password_reset_done.html'
        ), 
        name='password_reset_done'),
    path('reset/<uidb64>/<token>/', 
        auth_views.PasswordResetConfirmView.as_view(
            template_name='authentication/password_reset_confirm.html'
        ), 
        name='password_reset_confirm'),
    path('reset/complete/', 
        auth_views.PasswordResetCompleteView.as_view(
            template_name='authentication/password_reset_complete.html'
        ), 
        name='password_reset_complete'),
]