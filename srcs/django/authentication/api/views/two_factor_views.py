from ...services.two_factor_service import TwoFactorService
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login as auth_login
from django.http import JsonResponse
from django.views import View
import json
import logging

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name="dispatch")
class Enable2FAView(View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "No autorizado"}, status=401)

        try:
            TwoFactorService.enable_2fa(request.user)
            return JsonResponse({"message": "2FA activado correctamente"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


@method_decorator(csrf_exempt, name="dispatch")
class Verify2FAAPIView(View):
    def post(self, request, *args, **kwargs):
        is_valid, user = TwoFactorService.verify_session(
            request.session.get("pending_user_id"),
            request.session.get("user_authenticated", False),
        )

        if not is_valid:
            logger.warning("Invalid 2FA session")
            return JsonResponse({"error": "Sesión inválida"}, status=401)

        try:
            # data expected to be in JSON format
            if hasattr(request, "data"):
                data = request.data
            else:
                try:
                    data = json.loads(request.body)
                except json.JSONDecodeError:
                    # if the data is not in JSON format, try to get it from POST
                    data = request.POST

            # Obtaining the verification code from the request
            code = data.get("code")
            
            if not code:
                logger.warning(f"No code provided for user {user.id}")
                return JsonResponse({"error": "Código no proporcionado"}, status=400)
                
            logger.info(f"Attempting 2FA verification for user {user.id}")
            
            # Verifying the 2FA code
            if TwoFactorService.verify_2fa_code(user, code):
                # Cleaning the session keys
                TwoFactorService.clean_session_keys(request.session)
                auth_login(request, user)
                request.session["is_2fa_verified"] = True
                
                logger.info(f"2FA verification successful for user {user.id}")
                
                return JsonResponse(
                    {
                        "status": "success",
                        "message": "Código verificado correctamente",
                        "username": user.username,
                        "session_id": request.session.session_key,
                    }
                )
            
            logger.warning(f"2FA verification failed for user {user.id}")
            return JsonResponse({"error": "Código inválido o expirado"}, status=400)
        except Exception as e:
            logger.error(f"Error in 2FA verification for user {getattr(user, 'id', 'unknown')}: {str(e)}", exc_info=True)
            return JsonResponse({"error": str(e)}, status=400)


@method_decorator(csrf_exempt, name="dispatch")
class Disable2FAView(View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "No autorizado"}, status=401)

        try:
            TwoFactorService.disable_2fa(request.user)
            return JsonResponse({"message": "2FA desactivado correctamente"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
