from ninja import Schema
from typing import Optional, Dict
from pydantic import Field
from django.core.files import File
import base64

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

class GDPRSchema(Schema):
    accept_terms: bool
    accept_cookies: bool

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

class ProfileSchema(Schema):
    email: Optional[str]
    password: Optional[str]

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

class ProfileImageResponseSchema(BaseSchema):
    status: str
    message: str
    data: Dict[str, Optional[str]]

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

class UserProfileResponseSchema(Schema):
    user: UserProfileSchema
    show_qr: bool