from ninja import Router, File, UploadedFile
from typing import Dict
from ..schemas import *
from ..views import *
from django.http import JsonResponse
from authentication.services import ProfileService
import base64
from django.core.files.base import ContentFile

router = Router()

# Auth endpoints
@router.post("/login", tags=["auth"])
def login(request, data: AuthSchema) -> Dict:
    """Iniciar sesión de usuario"""
    request.data = data.dict()
    return LoginAPIView.as_view()(request)

@router.post("/register", tags=["auth"])
def register(request, data: RegisterSchema) -> Dict:
    """Registrar nuevo usuario"""
    try:        
        request.data = data.dict()
        response = RegisterAPIView.as_view()(request)

        return response
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error en registro: {str(e)}'
        }, status=400)

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

# @router.get("/profile", tags=["profile"])
# def get_profile(request) -> Dict:
#     """Ver perfil del usuario"""
#     return ProfileAPIView.as_view()(request)

@router.put("/profile", tags=["profile"], response=ProfileImageResponseSchema)
def update_profile(request, data: ProfileUpdateSchema) -> Dict:
    """Actualizar perfil básico"""
    try:
        if data.profile_image_base64:
            try:
                format, imgstr = data.profile_image_base64.split(';base64,')
                ext = format.split('/')[-1]
                profile_image = ContentFile(
                    base64.b64decode(imgstr), 
                    name=f'profile_{request.user.id}.{ext}'
                )
                request.FILES['profile_image'] = profile_image
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Error procesando imagen: {str(e)}'
                }, status=400)

        result = ProfileService.update_profile(
            user=request.user,
            data={'email': data.email} if data.email else {},
            files=request.FILES
        )
        
        return {
            'status': 'success',
            'message': 'Perfil actualizado correctamente',
            'data': result
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }

@router.post("/profile/password", tags=["profile"])
def change_password(request, data: PasswordChangeSchema) -> Dict:
    """Cambiar contraseña"""
    request.data = data.dict()
    return EditProfileAPIView.as_view()(request)

@router.post("/profile/email", tags=["profile"])
def change_email(request, data: EmailChangeSchema) -> Dict:
    """Cambiar email"""
    request.data = data.dict()
    return EditProfileAPIView.as_view()(request)

@router.post("/profile/restore-image", tags=["profile"])
def restore_image(request, data: RestoreImageSchema) -> Dict:
    """Restaurar imagen de perfil"""
    request.data = data.dict()
    return EditProfileAPIView.as_view()(request)

@router.post("/profile/image", tags=["profile"])
def update_profile_image(
    request, 
    profile_image: UploadedFile
) -> Dict:
    """Actualizar imagen de perfil"""
    request.FILES = {'profile_image': profile_image}
    return EditProfileAPIView.as_view()(request)

@router.delete("/profile", tags=["profile"])
def delete_account(request, data: DeleteAccountSchema) -> Dict:
    """Eliminar cuenta"""
    request.data = data.dict()
    return DeleteAccountAPIView.as_view()(request)

@router.get("/profile/user", tags=["profile"])
def get_user_profile(request) -> Dict:
    """Ver perfil de otro usuario"""
    return UserProfileAPIView.as_view()(request)

# Password endpoints
@router.post("/password/reset", tags=["password"])
def password_reset(request, data: PasswordResetSchema) -> Dict:
    """Solicitar reset de contraseña"""
    request.data = data.dict()
    return PasswordResetAPIView.as_view()(request)

@router.post("/password/reset/confirm", tags=["password"])
def password_reset_confirm(request, data: PasswordResetConfirmSchema) -> Dict:
    """Confirmar reset de contraseña"""
    request.data = data.dict()
    return PasswordResetConfirmAPIView.as_view()(request)

# Email verification endpoints
@router.post("/verify-email/{uidb64}/{token}", tags=["email"])
def verify_email(request, uidb64: str, token: str) -> Dict:
    """Verificar email"""
    request.data = {'uidb64': uidb64, 'token': token}
    return VerifyEmailAPIView.as_view()(request)

@router.post("/verify-email-change/{uidb64}/{token}", tags=["email"])
def verify_email_change(request, uidb64: str, token: str) -> Dict:
    """Verificar cambio de email"""
    request.data = {'uidb64': uidb64, 'token': token}
    return VerifyEmailChangeAPIView.as_view()(request)

# QR endpoints

@router.get("/qr/generate/{username}", tags=["2fa"])
def generate_qr(request, username: str) -> Dict:
    """Generar QR para 2FA"""
    return GenerateQRAPIView.as_view()(request, username=username)

@router.post("/qr/validate", tags=["2fa"])
def validate_qr(request, data: QRSchema) -> Dict:
    """Validar código QR"""
    request.data = data.dict()
    return ValidateQRAPIView.as_view()(request)

# 2FA endpoints

@router.post("/2fa/enable", tags=["2fa"])
def enable_2fa(request) -> Dict:
    """Activar 2FA"""
    return Enable2FAView.as_view()(request)

@router.post("/2fa/verify", tags=["2fa"])
def verify_2fa(request, data: TwoFactorSchema) -> Dict:
    """Verificar código 2FA"""
    request.data = data.dict()
    return Verify2FAAPIView.as_view()(request)

@router.post("/2fa/disable", tags=["2fa"])
def disable_2fa(request) -> Dict:
    """Desactivar 2FA"""
    return Disable2FAView.as_view()(request)

