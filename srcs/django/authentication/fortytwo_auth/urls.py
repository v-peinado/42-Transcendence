# authentication/fortytwo_auth/urls.py
from django.urls import path
from . import views

app_name = 'fortytwo_auth'  # Añadimos el namespace

urlpatterns = [
    path('42/login/', views.fortytwo_login, name='login'),  # Mantenemos el nombre simple 'login'
    path('42/callback/', views.fortytwo_callback, name='ft_callback'),
    path('api/42/login/', views.FortyTwoAuthAPIView.as_view(), name='api_ft_login'),
    path('api/42/callback/', views.FortyTwoCallbackAPIView.as_view(), name='api_ft_callback'),
]