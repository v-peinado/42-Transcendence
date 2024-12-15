from ninja import Router
from typing import Dict, Any
from django.http import HttpResponse
from ..schemas import *
from ..views import *


router = Router()

# Endpoint de prueba
@router.get("/hello")
def hello_world(request) -> Dict[str, Any]:
    return {"message": "Hello World"}

# Auth endpoints
@router.post("/login", tags=["auth"])
def login(request, data: AuthSchema) -> Dict:
    """Iniciar sesión de usuario"""
    return LoginAPIView.as_view()(request, data=data.dict())

@router.post("/register", tags=["auth"])
def register(request, data: RegisterSchema) -> Dict:
    """Registrar nuevo usuario"""
    return RegisterAPIView.as_view()(request, data=data.dict())

@router.post("/logout", tags=["auth"])
def logout(request) -> Dict:
    """Cerrar sesión de usuario"""
    return LogoutAPIView.as_view()(request)

# GDPR endpoints
@router.get("/gdpr/settings", tags=["gdpr"])
def gdpr_settings(request) -> Dict:
    """Obtener configuración GDPR"""
    return GDPRSettingsAPIView.as_view()(request)

@router.get("/gdpr/export", tags=["gdpr"])
def export_data(request) -> Dict:
    """Exportar datos personales"""
    return ExportPersonalDataAPIView.as_view()(request)

@router.get("/gdpr/privacy", tags=["gdpr"])
def privacy_policy(request) -> Dict:
    """Ver política de privacidad"""
    return PrivacyPolicyAPIView.as_view()(request)

# Profile endpoints
@router.get("/profile", tags=["profile"])
def get_profile(request) -> Dict:
    """Ver perfil de usuario"""
    return ProfileAPIView.as_view()(request)

@router.get("/profile/user", tags=["profile"])
def get_user_profile(request) -> Dict:
    """Ver perfil de otro usuario"""
    return UserProfileAPIView.as_view()(request)

@router.delete("/profile", tags=["profile"])
def delete_account(request) -> Dict:
    """Eliminar cuenta"""
    return DeleteAccountAPIView.as_view()(request)

# Password endpoints
@router.post("/password/reset", tags=["password"])
def password_reset(request, data: PasswordResetSchema) -> Dict:
    """Solicitar reset de contraseña"""
    return PasswordResetAPIView.as_view()(request, data=data.dict())

@router.post("/password/reset/confirm", tags=["password"])
def password_reset_confirm(request, data: PasswordResetConfirmSchema) -> Dict:
    """Confirmar reset de contraseña"""
    return PasswordResetConfirmAPIView.as_view()(request, data=data.dict())

# Email verification endpoints
@router.post("/verify-email/{uidb64}/{token}", tags=["email"])
def verify_email(request, uidb64: str, token: str) -> Dict:
    """Verificar email"""
    return VerifyEmailAPIView.as_view()(request, uidb64=uidb64, token=token)

@router.post("/verify-email-change/{uidb64}/{token}", tags=["email"])
def verify_email_change(request, uidb64: str, token: str) -> Dict:
    """Verificar cambio de email"""
    return VerifyEmailChangeAPIView.as_view()(request, uidb64=uidb64, token=token)

# 2FA endpoints
@router.get("/qr/generate/{username}", tags=["2fa"])
def generate_qr(request, username: str) -> Dict:
    """Generar QR para 2FA"""
    return GenerateQRAPIView(request, username)

@router.post("/qr/validate", tags=["2fa"])
def validate_qr(request, data: QRSchema) -> Dict:
    """Validar código QR"""
    return ValidateQRAPIView(request, data=data.dict())

@router.post("/2fa/enable", tags=["2fa"])
def enable_2fa(request) -> Dict:
    """Activar 2FA"""
    return Enable2FAView(request)

@router.post("/2fa/verify", tags=["2fa"])
def verify_2fa(request, data: TwoFactorSchema) -> Dict:
    """Verificar código 2FA"""
    return Verify2FAAPIView(request, data=data.dict())

@router.post("/2fa/disable", tags=["2fa"])
def disable_2fa(request) -> Dict:
    """Desactivar 2FA"""
    return Disable2FAView(request)

