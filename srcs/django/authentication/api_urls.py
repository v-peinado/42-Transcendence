from django.urls import path
from .api_views import (
    GenerateQRCodeView, 
    ValidateQRCodeView, 
    LoginView, 
    LogoutView,
    RegisterView  # Incluimos la nueva vista de registro
)

urlpatterns = [
    path('generate_qr/<str:username>/', GenerateQRCodeView.as_view(), name='generate_qr'),
    path('validate_qr/', ValidateQRCodeView.as_view(), name='validate_qr'),
    path('login/', LoginView.as_view(), name='api_login'),
    path('logout/', LogoutView.as_view(), name='api_logout'),
    path('register/', RegisterView.as_view(), name='api_register'),  # Nueva ruta para registro
]