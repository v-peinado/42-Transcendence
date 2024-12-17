from ninja import Schema
from typing import Optional

class AuthSchema(Schema):
    username: str
    password: str
    remember: Optional[bool] = False

class RegisterSchema(Schema):
    username: str
    email: str
    password1: str
    password2: str

class GDPRSchema(Schema):
    accept_terms: bool
    accept_cookies: bool

class ProfileSchema(Schema):
    email: Optional[str]
    password: Optional[str]

class QRSchema(Schema):
    code: str

class TokenSchema(Schema):
    uidb64: str
    token: str

class PasswordResetSchema(Schema):
    email: str

class PasswordResetConfirmSchema(Schema):
    new_password1: str
    new_password2: str
    uidb64: str
    token: str

class TwoFactorSchema(Schema):
    code: str