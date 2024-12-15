from django.urls import path
from . import views

app_name = 'web_fortytwo_auth'

urlpatterns = [
    # Rutas web
    path('login/', views.fortytwo_login, name='login'),
    path('callback/', views.fortytwo_callback, name='ft_callback'),
    
    # Rutas API
    path('api/login/', views.FortyTwoAuthAPIView.as_view(), name='api_ft_login'),
    path('api/callback/', views.FortyTwoCallbackAPIView.as_view(), name='api_ft_callback'),
]
