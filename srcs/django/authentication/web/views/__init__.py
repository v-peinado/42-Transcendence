from .auth_views import home, login, register, logout
from .gdpr_views import gdpr_settings, export_personal_data, privacy_policy
from .password_views import CustomPasswordResetView, CustomPasswordResetConfirmView
from .profile_views import edit_profile, user, delete_account
from .verification_views import (
    verify_email, verify_email_change,
    enable_2fa, verify_2fa, disable_2fa,
    generate_qr, validate_qr
)

__all__ = [
	'home', 'login', 'register', 'logout',
	'gdpr_settings', 'export_personal_data', 'privacy_policy',
	'CustomPasswordResetView', 'CustomPasswordResetConfirmView',
	'edit_profile', 'user', 'delete_account',
	'verify_email', 'verify_email_change',
	'enable_2fa', 'verify_2fa', 'disable_2fa',
	'generate_qr', 'validate_qr'
]