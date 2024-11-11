from django.urls import path
from . import views
from .api_views import GenerateQRCodeView, ValidateQRCodeView, LoginView, LogoutView

urlpatterns = [
    # Vistas tradicionales
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('user/', views.user, name='user'),
    
    # Rutas API
    path('api/generate_qr/<str:username>/', GenerateQRCodeView.as_view(), name='generate_qr'),
    path('api/validate_qr/', ValidateQRCodeView.as_view(), name='validate_qr'),
    path('api/login/', LoginView.as_view(), name='api_login'),
    path('api/logout/', LogoutView.as_view(), name='api_logout'),
]