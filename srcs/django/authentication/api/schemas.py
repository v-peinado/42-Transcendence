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

# Token schemas

class TokenSchema(Schema):
    uidb64: str
    token: str

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
    
class ProfileUpdateSchema(BaseSchema):
    email: Optional[str] = None
    profile_image_base64: Optional[str] = None

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