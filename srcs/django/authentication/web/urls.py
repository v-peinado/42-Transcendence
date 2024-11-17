from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('user/', views.user, name='user'),
    path('logout/', views.custom_logout, name='logout'),
    path('auth/42/', include('authentication.fortytwo_auth.urls', namespace='web_fortytwo_auth')),
    path('generate_qr/<str:username>/', views.generate_qr, name='generate_qr'),
    path('validate_qr/', views.validate_qr, name='validate_qr'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
]