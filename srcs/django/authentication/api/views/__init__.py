from .auth_views import (
    LoginAPIView,
    LogoutAPIView,
    RegisterAPIView,
    GenerateQRAPIView,
    ValidateQRAPIView
)
from .profile_views import *
from .password_views import *
from .gdpr_views import *
from .verification_views import *
from .fortytwo_views import *

__all__ = [
    'LoginAPIView',
    'LogoutAPIView',
    'RegisterAPIView',
    'GenerateQRAPIView',
    'ValidateQRAPIView'
]