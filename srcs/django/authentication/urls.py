from django.urls import path, include
from . import views

urlpatterns = [
    # Vistas tradicionales
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('user/', views.user, name='user'),
    
    # Incluir rutas API - Corregida la ruta
    path('api/', include('authentication.api_urls')),
]