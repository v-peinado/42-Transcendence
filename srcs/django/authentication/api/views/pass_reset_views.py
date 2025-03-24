from ...services.password_service import PasswordService
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views import View
import json


@method_decorator(csrf_exempt, name="dispatch")
class PasswordResetAPIView(View):
    """API for password reset requests"""

    def post(self, request, *args, **kwargs):
        try:
            # Get request data
            if hasattr(request, "data"):
                data = request.data
            else:
                data = json.loads(request.body)

            email = data.get("email", "").strip().lower()
            if not email:
                return JsonResponse(
                    {"status": "error", "message": "Email no proporcionado"},
                    status=400
                )
                
            # Generate token and verification data
            token_data = PasswordService.initiate_password_reset(email)

            if token_data:
                return JsonResponse(
                    {
                        "status": "success",
                        "message": "Se ha enviado un email con instrucciones",
                        "data": {
                            "uidb64": token_data["uid"],
                            "token": token_data["token"],
                        },
                    }
                )

            return JsonResponse(
                {
                    "status": "success",
                    "message": "Si el email existe, recibirás instrucciones",
                }
            )

        except ValidationError as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "message": "Invalid JSON data"}, status=400
            )


@method_decorator(csrf_exempt, name="dispatch")
class PasswordResetConfirmAPIView(View):
    def post(self, request, *args, **kwargs):
        """Confirm password reset with token (No authentication required)"""
        try:
            if hasattr(request, "data"):
                data = request.data
            else:
                data = json.loads(request.body)

            result = PasswordService.confirm_password_reset(
                data.get("uidb64"),
                data.get("token"),
                data.get("new_password1"),
                data.get("new_password2"),
            )
            return JsonResponse(
                {
                    "status": "success",
                    "message": "Contraseña restablecida correctamente",
                }
            )
        except ValidationError as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "message": "Invalid JSON data"}, status=400
            )
