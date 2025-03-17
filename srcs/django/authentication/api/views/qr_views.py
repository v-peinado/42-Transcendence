from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login as auth_login
from django.http import HttpResponse, JsonResponse
from ...services.qr_service import QRService
from django.views import View
import logging
import json

logger = logging.getLogger(__name__)
qr_service = QRService()


@method_decorator(csrf_exempt, name="dispatch")
class GenerateQRAPIView(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {"status": "error", "message": "No autorizado"}, status=401
            )

        try:
            buffer = qr_service.generate_qr(request.user.username)
            return HttpResponse(
                buffer.getvalue(),
                content_type="image/png",
                headers={"Cache-Control": "no-store"},
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)


@method_decorator(csrf_exempt, name="dispatch")
class ValidateQRAPIView(View):
    def __init__(self):
        super().__init__()
        self._qr_service = QRService()

    def post(self, request):
        try:
            # Deserialize JSON
            data = json.loads(request.body.decode('utf-8'))
            
            # First validation: get username and validate QR
            success, message, username = self._qr_service.pre_validate_qr(data)
            if not success:
                return JsonResponse({"error": message}, status=400)
                
            # Second validation: authenticate user
            success, result, redirect_url = self._qr_service.authenticate_qr(username)
            if not success:
                return JsonResponse({"error": result}, status=400)

            if redirect_url == "/verify-2fa/":
                # Special case: 2FA required
                request.session.update({
                    "pending_user_id": result.id,
                    "user_authenticated": True,
                    "manual_user": not result.is_fortytwo_user,
                    "fortytwo_user": result.is_fortytwo_user,
                })
                return JsonResponse({
                    "success": True,
                    "require_2fa": True, 
                    "redirect_url": redirect_url
                })
            else:
                # Successful authentication
                auth_login(request, result) # result is the user in this case
                return JsonResponse({
                    "success": True,
                    "redirect_url": redirect_url
                })

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            logger.error(f"QR validation error: {str(e)}", exc_info=True)
            return JsonResponse({"error": str(e)}, status=400)
