from django.urls import path, include
from .views import (
    GenerateQRCodeView, 
    ValidateQRCodeView, 
    LoginView, 
    LogoutView,
    RegisterView,
    EditProfileView,
    DeleteAccountView
)

# URLs específicas de autenticación
auth_patterns = [
    path('generate_qr/<str:username>/', GenerateQRCodeView.as_view(), name='generate_qr'),
    path('validate_qr/', ValidateQRCodeView.as_view(), name='validate_qr'),
    path('login/', LoginView.as_view(), name='api_login'),
    path('logout/', LogoutView.as_view(), name='api_logout'),
    path('register/', RegisterView.as_view(), name='api_register'),
    path('edit-profile/', EditProfileView.as_view(), name='api_edit_profile'),
    path('delete-account/', DeleteAccountView.as_view(), name='api_delete_account'),
    path('42/', include('authentication.fortytwo_auth.urls')),
]

# Patrón principal que incluye todas las rutas de autenticación
urlpatterns = [
    path('authentication/', include((auth_patterns, 'authentication'), namespace='auth_api')),
]

# Notas:
# Las rutas serán accesibles a través de http://localhost:8000/api/authentication/
# de esta forma, las rutas ahora son:
# - /api/authentication/generate_qr/<str:username>/
# - /api/authentication/validate_qr/
# - /api/authentication/login/
# - /api/authentication/logout/
# - /api/authentication/register/
# - /api/authentication/edit-profile/
# - /api/authentication/delete-account/
# - /api/authentication/42/ -->>> /api/authentication/42/api/42/login/ y /api/authentication/42/api/42/callback/

# Para acceder a la vista de generación de QR, se debe hacer una petición GET a /api/authentication/generate_qr/<str:username>/
# Para acceder a la vista de validación de QR, se debe hacer una petición POST a /api/authentication/validate_qr/
# Para acceder a la vista de login, se debe hacer una petición POST a /api/authentication/login/
# Para acceder a la vista de logout, se debe hacer una petición POST a /api/authentication/logout/
# Para acceder a la vista de registro, se debe hacer una petición POST a /api/authentication/register/
# Para acceder a la vista de edición de perfil, se debe hacer una petición POST a /api/authentication/edit-profile/
# Para acceder a la vista de eliminación de cuenta, se debe hacer una petición POST a /api/authentication/delete-account/
# Para acceder a la vista de autenticación con 42, se debe hacer una petición GET a /api/authentication/42/
