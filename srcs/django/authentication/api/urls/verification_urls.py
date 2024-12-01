from django.urls import path
from ..views.verification_views import (
    GenerateQRCodeAPIView,
    ValidateQRCodeAPIView
)
from ...web.views import (
    verify_email,
    verify_email_change,
    enable_2fa,
    verify_2fa,
    disable_2fa
)

urlpatterns = [
    # Verificación de email
    path('verify-email/<str:uidb64>/<str:token>/', 
         verify_email, 
         name='api_verify_email'),
    
    path('verify-email-change/<str:uidb64>/<str:token>/', 
         verify_email_change, 
         name='api_verify_email_change'),
    
    # Autenticación de dos factores (2FA)
    path('enable-2fa/', 
         enable_2fa, 
         name='api_enable_2fa'),
    
    path('verify-2fa/', 
         verify_2fa, 
         name='api_verify_2fa'),
    
    path('disable-2fa/', 
         disable_2fa, 
         name='api_disable_2fa'),
    
    # QR Code
    path('generate-qr/<str:username>/', 
         GenerateQRCodeAPIView.as_view(), 
         name='api_generate_qr'),
    
    path('validate-qr/', 
         ValidateQRCodeAPIView.as_view(), 
         name='api_validate_qr'),
]