from .auth_views import LoginAPIView, LogoutAPIView, RegisterAPIView
from .gdpr_views import GDPRSettingsAPIView, ExportPersonalDataAPIView, PrivacyPolicyAPIView, DeleteAccountAPIView
from .profile_views import ProfileAPIView, ProfileImageAPIView, DeleteAccountView
from .password_views import PasswordChangeAPIView, PasswordResetAPIView, PasswordResetConfirmAPIView
from .verification_views import (
    Enable2FAView,
    Verify2FAAPIView,
    Disable2FAView,
    VerifyEmailView,
    GenerateQRCodeAPIView,
    ValidateQRCodeAPIView
)

__all__ = [
    # Verification views
    'Enable2FAView',
    'Verify2FAAPIView',
    'Disable2FAView',
    'VerifyEmailView',
    'GenerateQRCodeAPIView',
    'ValidateQRCodeAPIView',
	
    # Auth views
    'LoginAPIView',
    'LogoutAPIView', 
    'RegisterAPIView',

    # GDPR views
    'GDPRSettingsAPIView',
    'ExportPersonalDataAPIView',
    'PrivacyPolicyAPIView',
    'DeleteAccountAPIView',

    # Profile views
    'ProfileAPIView',
    'ProfileImageAPIView',
    'DeleteAccountView',
    
    # Password views
    'PasswordChangeAPIView',
    'PasswordResetAPIView',
    'PasswordResetConfirmAPIView'
]