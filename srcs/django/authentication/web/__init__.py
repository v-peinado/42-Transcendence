from .views.auth_views import login, register, logout
from .views.profile_views import edit_profile, delete_account
from .views.password_views import CustomPasswordResetView

__all__ = [
    'login', 'register', 'logout',
    'edit_profile', 'delete_account',
    'CustomPasswordResetView'
]