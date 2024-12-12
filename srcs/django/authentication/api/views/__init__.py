from .auth_views import LoginAPIView, LogoutAPIView, RegisterAPIView
from .gdpr_views import GDPRSettingsAPIView, ExportPersonalDataAPIView, PrivacyPolicyAPIView, DeleteAccountAPIView
from .profile_views import ProfileAPIView, ProfileImageAPIView, DeleteAccountView
from .pass_reset_views import PasswordChangeAPIView, PasswordResetAPIView, PasswordResetConfirmAPIView
from .verify_email_views import VerifyEmailAPIView, VerifyEmailChangeAPIView
from .two_factor_views import Enable2FAView, Verify2FAAPIView, Disable2FAView
from .qr_views import GenerateQRAPIView, ValidateQRAPIView

__all__ = [
    # Verification email views
    'VerifyEmailAPIView',
	'VerifyEmailChangeAPIView',

	# Two factor views
    'Enable2FAView',
    'Verify2FAAPIView',
    'Disable2FAView',

	# QR code views
    'GenerateQRAPIView',
    'ValidateQRAPIView',
	
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
    
    # Pass_reset views
    'PasswordChangeAPIView',
    'PasswordResetAPIView',
    'PasswordResetConfirmAPIView'
]