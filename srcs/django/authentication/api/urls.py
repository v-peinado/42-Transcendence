from django.urls import path, include
from .views import (
    GenerateQRCodeView, 
    ValidateQRCodeView, 
    LoginView, 
    LogoutView,
    RegisterView  
)

urlpatterns = [
    path('generate_qr/<str:username>/', GenerateQRCodeView.as_view(), name='generate_qr'),
    path('validate_qr/', ValidateQRCodeView.as_view(), name='validate_qr'),
    path('login/', LoginView.as_view(), name='api_login'),
    path('logout/', LogoutView.as_view(), name='api_logout'),
    path('register/', RegisterView.as_view(), name='api_register'),
    # Ruta para 42
    path('auth/42/', include('authentication.fortytwo_auth.urls')),
]