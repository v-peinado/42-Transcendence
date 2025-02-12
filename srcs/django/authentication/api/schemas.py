from ninja import Schema
from typing import Optional, Dict

# Auth schemas


class AuthSchema(Schema):
    username: str
    password: str
    remember: Optional[bool] = False


class RegisterSchema(Schema):
    username: str
    email: str
    password1: str
    password2: str
    privacy_policy: bool = False


# GDPR schemas


class GDPRExportSchema(Schema):
    status: str
    data: Dict
    download_url: str


# QR schemas


class QRSchema(Schema):
    username: str


# Password schemas


class PasswordResetSchema(Schema):
    email: str


class PasswordResetConfirmSchema(Schema):
    new_password1: str
    new_password2: str
    uidb64: str
    token: str


# Two factor schemas


class TwoFactorSchema(Schema):
    code: str


# Profile schemas


class BaseSchema(Schema):
    class Config:
        arbitrary_types_allowed = True


class PasswordChangeSchema(BaseSchema):
    current_password: str
    new_password1: str
    new_password2: str


class EmailChangeSchema(BaseSchema):
    email: str


class RestoreImageSchema(BaseSchema):
    restore_image: bool = True


class DeleteAccountSchema(BaseSchema):
    confirm_password: str


class UserProfileSchema(Schema):
    id: int
    username: str
    email: str
    is_active: bool
    is_fortytwo_user: bool
    email_verified: bool
    two_factor_enabled: bool
    profile_image_url: Optional[str]
    date_joined: Optional[str]
    last_login: Optional[str]
    show_qr: bool


# Auth schemas 42
class FortyTwoAuthResponseSchema(Schema):
    status: str
    auth_url: Optional[str]
    message: Optional[str]
    user: Optional[Dict] = None


# Auth schemas 42
class FortyTwoCallbackRequestSchema(Schema):
    code: str = None
    state: Optional[str] = None


class FortyTwoCallbackResponseSchema(Schema):
    status: str
    message: str
    user: Optional[Dict]
    require_2fa: Optional[bool] = False
