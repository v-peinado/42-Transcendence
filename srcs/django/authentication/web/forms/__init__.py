from .auth_forms import RegistrationForm
from .profile_forms import ProfileUpdateForm
from .password_forms import PasswordChangeForm
from .gdpr_forms import DeleteAccountForm

__all__ = [
    'RegistrationForm',
    'ProfileUpdateForm',
    'PasswordChangeForm',
    'DeleteAccountForm'
]