from authentication.fortytwo_auth.views import FortyTwoLoginAPIView, FortyTwoCallbackAPIView
from authentication.services import ProfileService
from ninja import Router, UploadedFile
from django.http import JsonResponse
from typing import Dict, Optional
from django.core.exceptions import ValidationError, PermissionDenied
from ..schemas import *
from ..views import *

# Authentication API Router Configuration

# This file defines all API endpoints related to user authentication and profile management
# using Django Ninja routers. It acts as the central entry point for all authentication-related
# HTTP requests in the application.

# Structure:
# Each endpoint is mapped to a Django view that implements the actual logic
# Request data is validated using schemas defined in ..schemas module.
# Responses are also validated using Django Ninja's response system.

router = Router()

# Auth endpoints
@router.post("/login", tags=["auth"])
def login(request, data: AuthSchema) -> Dict:
    """Login user"""
    request.data = data.dict()
    return LoginAPIView.as_view()(request)

@router.post("/register", tags=["auth"])
def register(request, data: RegisterSchema) -> Dict:
    """Register user"""
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
    """Logout user"""
    return LogoutAPIView.as_view()(request)

# 42 endpoints

@router.get("/auth/42", tags=["auth"], response=FortyTwoAuthResponseSchema)
def fortytwo_login(request) -> Dict:
    """42 Login"""
    return FortyTwoLoginAPIView.as_view()(request)

@router.get(
    "/auth/42/callback", 
    tags=["auth"],
    response=FortyTwoCallbackResponseSchema
)
def fortytwo_callback(
    request,
    code: str,
    state: Optional[str] = None
) -> Dict:
    """Callback 42 auth"""
    data = FortyTwoCallbackRequestSchema(code=code, state=state)
    return FortyTwoCallbackAPIView.as_view()(request, data)

# GDPR endpoints

# this is deprecated 
# we use the next one, this is just for compatibility developing part
@router.get("/gdpr/export", tags=["gdpr"], response=GDPRExportSchema)
def export_data(request) -> Dict:
    """Export personal data"""
    return ExportPersonalDataAPIView.as_view()(request)

@router.get("/gdpr/export/download", tags=["gdpr"])
def download_data(request) -> Dict:
    """Download personal data"""
    return ExportPersonalDataAPIView().get_download(request)

@router.get("/gdpr/privacy", tags=["gdpr"])
def privacy_policy(request) -> Dict:
    """See privacy policy"""
    return PrivacyPolicyAPIView.as_view()(request)

# Profile endpoints

@router.post("/profile/password", tags=["profile"])
def change_password(request, data: PasswordChangeSchema) -> Dict:
    """Change user password """
    request.data = data.dict()
    return EditProfileAPIView.as_view()(request)

@router.post("/profile/email", tags=["profile"])
def change_email(request, data: EmailChangeSchema) -> Dict:
    """Change user email"""
    request.data = data.dict()
    return EditProfileAPIView.as_view()(request)

@router.post("/profile/restore-image", tags=["profile"])
def restore_image(request, data: RestoreImageSchema) -> Dict:
    """Restore profile image"""
    request.data = data.dict()
    return EditProfileAPIView.as_view()(request)

@router.post("/profile/image", tags=["profile"])
def update_profile_image(request, profile_image: UploadedFile) -> Dict:
    """Update profile image"""
    try:
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 'error',
                'message': 'Autenticación requerida'
            }, status=401)
            
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
    except ValidationError as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    except PermissionDenied as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=403)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@router.post("/profile/delete", tags=["profile"])
def delete_account(request, data: DeleteAccountSchema) -> Dict:
    """Delete user account (soft delete GDPR)"""
    try:
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 'error',
                'message': 'Autenticación requerida'
            }, status=401)
            
        result = ProfileService.delete_user_account(
            user=request.user,
            password=data.confirm_password if not request.user.is_fortytwo_user else None
        )
        return {
            'status': 'success',
            'message': 'Cuenta eliminada correctamente'
        }
    except ValidationError as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    except PermissionDenied as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=403)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@router.get("/profile/user", tags=["profile"], response=UserProfileSchema)
def get_user_profile(request) -> Dict:
    try:
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 'error',
                'message': 'Autenticación requerida'
            }, status=401)
            
        profile_data = ProfileService.get_user_profile_data(request.user)
        return {
            'id': profile_data['user'].id,
            'username': profile_data['user'].username,
            'email': profile_data['user'].email,
            'is_active': profile_data['user'].is_active,
            'is_fortytwo_user': profile_data['user'].is_fortytwo_user,
            'email_verified': profile_data['user'].email_verified,
            'two_factor_enabled': profile_data['user'].two_factor_enabled,
            'profile_image_url': profile_data['user'].profile_image.url if profile_data['user'].profile_image else None,
            'date_joined': profile_data['user'].date_joined.isoformat() if profile_data['user'].date_joined else None,
            'last_login': profile_data['user'].last_login.isoformat() if profile_data['user'].last_login else None,
            'show_qr': profile_data['show_qr']
        }
    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except PermissionDenied as e:
        return JsonResponse({'error': str(e)}, status=403)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Password endpoints
@router.post("/password/reset", tags=["password"])
def password_reset(request, data: PasswordResetSchema) -> Dict:
    """Reset user password"""
    request.data = data.dict()
    return PasswordResetAPIView.as_view()(request)

@router.post("/password/reset/confirm", tags=["password"])
def password_reset_confirm(request, data: PasswordResetConfirmSchema) -> Dict:
    """Confirm password reset"""
    request.data = data.dict()
    return PasswordResetConfirmAPIView.as_view()(request)

# QR endpoints

@router.get("/qr/generate", tags=["2fa"])
def generate_qr(request) -> Dict:
    """Generate QR code to authenticate"""
    return GenerateQRAPIView.as_view()(request)

@router.post("/qr/validate", tags=["2fa"])
def validate_qr(request, data: QRSchema) -> Dict:
    """Validate QR code to login"""
    request.data = data.dict()
    return ValidateQRAPIView.as_view()(request)

# 2FA endpoints

@router.post("/2fa/enable", tags=["2fa"])
def enable_2fa(request) -> Dict:
    """Enable 2FA"""
    return Enable2FAView.as_view()(request)

@router.post("/2fa/verify", tags=["2fa"])
def verify_2fa(request, data: TwoFactorSchema) -> Dict:
    """Verify 2FA"""
    request.data = data.dict()
    return Verify2FAAPIView.as_view()(request)

@router.post("/2fa/disable", tags=["2fa"])
def disable_2fa(request) -> Dict:
    """Disable 2FA"""
    return Disable2FAView.as_view()(request)

