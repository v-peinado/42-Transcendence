from django.urls import path
from ..views.auth_views import (
    LoginAPIView, LogoutAPIView, RegisterAPIView,
    GenerateQRAPIView, ValidateQRAPIView
)

urlpatterns = [
    path('login/', LoginAPIView.as_view(), name='api_login'),
    path('logout/', LogoutAPIView.as_view(), name='api_logout'),
    path('register/', RegisterAPIView.as_view(), name='api_register'),
    path('generate_qr/<str:username>/', GenerateQRAPIView.as_view(), name='api_generate_qr'),
    path('validate_qr/', ValidateQRAPIView.as_view(), name='api_validate_qr'),
]