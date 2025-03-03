from .auth_views import home, login, register, logout
from .gdpr_views import gdpr_settings, export_personal_data, privacy_policy
from .pass_reset_views import CustomPasswordResetView, CustomPasswordResetConfirmView
from .profile_views import EditProfileView, UserProfileView, DeleteAccountView
from .two_factor_views import enable_2fa, verify_2fa, disable_2fa
from .verify_email_views import verify_email, verify_email_change
from .qr_views import generate_qr, validate_qr


__all__ = [
    "home",
    "login",
    "register",
    "logout",
    "gdpr_settings",
    "export_personal_data",
    "privacy_policy",
    "CustomPasswordResetView",
    "CustomPasswordResetConfirmView",
    "EditProfileView",
    "UserProfileView",
    "DeleteAccountView",
    "verify_email",
    "verify_email_change",
    "enable_2fa",
    "verify_2fa",
    "disable_2fa",
    "generate_qr",
    "validate_qr",
]
