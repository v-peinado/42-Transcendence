from django.urls import path
from ..views.password_views import (
    PasswordResetAPIView,
    PasswordResetConfirmAPIView,
    PasswordChangeAPIView
)

urlpatterns = [
    path('password/reset/', 
        PasswordResetAPIView.as_view(), 
        name='api_password_reset'),
    path('password/reset/confirm/', 
        PasswordResetConfirmAPIView.as_view(), 
        name='api_password_reset_confirm'),
    path('password/change/', 
        PasswordChangeAPIView.as_view(), 
        name='api_password_change'),
]