from ninja import Router, UploadedFile
from typing import Dict
from ..schemas import *
from ..views import *
from django.http import JsonResponse
from authentication.services import ProfileService

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

@router.get("/gdpr/export", tags=["gdpr"], response=GDPRExportSchema)
def export_data(request) -> Dict:
    """Ver datos personales"""
    return ExportPersonalDataAPIView.as_view()(request)

@router.get("/gdpr/export/download", tags=["gdpr"])
def download_data(request) -> Dict:
    """Descargar datos personales del usuario autenticado"""
    return ExportPersonalDataAPIView().get_download(request)

@router.get("/gdpr/privacy", tags=["gdpr"])
def privacy_policy(request) -> Dict:
    """Ver política de privacidad"""
    return PrivacyPolicyAPIView.as_view()(request)

# Profile endpoints

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
def update_profile_image(request, profile_image: UploadedFile) -> Dict:
    """Actualizar imagen de perfil"""
    try:
        result = ProfileService.update_profile(
            user=request.user,
            data={},
            files={'profile_image': profile_image}
        )
        return {
            'status': 'success',
            'message': 'Imagen de perfil actualizada correctamente',
            'data': result
        }
    except Exception as e:
        return {
            'status': 'error', 
            'message': str(e)
        }

@router.post("/profile/delete", tags=["profile"])  # Cambiado de delete a post
def delete_account(request, data: DeleteAccountSchema) -> Dict:
    """Eliminar cuenta"""
    try:
        result = ProfileService.delete_user_account(
            user=request.user,
            password=data.confirm_password if not request.user.is_fortytwo_user else None
        )
        return {
            'status': 'success',
            'message': 'Cuenta eliminada correctamente'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }

@router.get("/profile/user", tags=["profile"], response=UserProfileResponseSchema)
def get_user_profile(request) -> Dict:
    """Ver perfil de otro usuario"""
    try:
        profile_data = ProfileService.get_user_profile_data(request.user)
        # Convertir datos a formato serializable
        return {
            'user': {
                'id': profile_data['user'].id,
                'username': profile_data['user'].username,
                'email': profile_data['user'].email,
                'is_active': profile_data['user'].is_active,
                'is_fortytwo_user': profile_data['user'].is_fortytwo_user,
                'email_verified': profile_data['user'].email_verified,
                'two_factor_enabled': profile_data['user'].two_factor_enabled,
                'profile_image_url': profile_data['user'].profile_image.url if profile_data['user'].profile_image else None,
                'date_joined': profile_data['user'].date_joined.isoformat() if profile_data['user'].date_joined else None,
                'last_login': profile_data['user'].last_login.isoformat() if profile_data['user'].last_login else None
            },
            'show_qr': profile_data['show_qr']
        }
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

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

# QR endpoints

@router.get("/qr/generate", tags=["2fa"])
def generate_qr(request) -> Dict:
    """Generar QR del usuario autenticado"""
    return GenerateQRAPIView.as_view()(request)

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

