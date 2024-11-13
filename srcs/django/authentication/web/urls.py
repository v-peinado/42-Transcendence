from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('user/', views.user, name='user'),
    path('logout/', views.custom_logout, name='logout'),
    path('auth/42/', include('authentication.fortytwo_auth.urls', namespace='fortytwo_auth')),
]