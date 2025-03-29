from authentication.fortytwo_auth.services.fortytwo_service import FortyTwoAuthService
from authentication.services.two_factor_service import TwoFactorService
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import login as auth_login
from django.core.exceptions import ValidationError, PermissionDenied
from authentication.models import CustomUser
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.views import View
import json


# Web Views
def fortytwo_login(request):
    """Web view for 42 login"""
    
    success, auth_url, error = FortyTwoAuthService.handle_login(request)
    if not success:
        messages.error(request, f"Error: {error}")
        return redirect("login")
    return redirect(auth_url)


def fortytwo_callback(request):
    """Web view for 42 callback"""
    
    success, message = FortyTwoAuthService.handle_callback(request)

    if not success:
        messages.error(request, message)
        return redirect("login")

    if message == "pending_2fa":
        return HttpResponseRedirect(reverse("verify_2fa"))

    return redirect("profile")


# API Views
class FortyTwoLoginAPIView(View):
    """API view for 42 login"""

    def get(self, request):
        try:
            success, auth_url, error = FortyTwoAuthService.handle_login(
                request, is_api=True
            )
            if success:
                return JsonResponse({"status": "success", "auth_url": auth_url})
            return JsonResponse({"status": "error", "message": error}, status=400)
        except PermissionDenied as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=403)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

# Decorator used to exempt the view from CSRF verification 
# Cross-Site Request Forgery or CSRF is a type of attack that occurs when a malicious web site, email, blog, instant message, 
# or program causes a user's web browser to perform an unwanted action on a trusted site when the user is authenticated.
@method_decorator(csrf_exempt, name="dispatch")
class FortyTwoCallbackAPIView(View):
    """API view for 42 callback"""

    def post(self, request):
        """Handle 42 callback for API"""
        try:
            data = json.loads(request.body)
            code = data.get("code")

            if not code:
                return JsonResponse(
                    {"status": "error", "message": "Código no proporcionado"},
                    status=400,
                )

            success, user, message = FortyTwoAuthService.handle_callback(
                request, is_api=True, code=code
            )

            if not success and message != "pending_2fa":
                return JsonResponse({"status": "error", "message": message}, status=400)

            if message == "pending_2fa":
                return JsonResponse(
                    {
                        "status": "success",
                        "message": "Por favor verifica el código 2FA",
                        "require_2fa": True,
                        "username": user.username,
                    }
                )

            return JsonResponse(
                {
                    "status": "success",
                    "message": "Login exitoso",
                    "username": user.username,
                }
            )

        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "message": "Formato JSON inválido"}, status=400
            )
        except ValidationError as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
        except PermissionDenied as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=403)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)


@method_decorator(csrf_exempt, name="dispatch")
class FortyTwoVerify2FAView(View):
    """View for verifying 2FA codes from 42 users"""

    def post(self, request):
        try:
            data = json.loads(request.body)
            code = data.get("code")

            if not code:
                return JsonResponse(
                    {"status": "error", "message": "Código no proporcionado"},
                    status=400,
                )

            # Verify that it's a 42 user with pending verification
            user_id = request.session.get("pending_user_id")
            is_fortytwo = request.session.get("fortytwo_user", False)

            if not user_id or not is_fortytwo:
                return JsonResponse(
                    {
                        "status": "error",
                        "message": "No hay verificación 2FA pendiente para usuario de 42",
                    },
                    status=401,
                )

            try:
                user = CustomUser.objects.get(id=user_id)
            except CustomUser.DoesNotExist:
                return JsonResponse(
                    {"status": "error", "message": "Usuario no encontrado"}, status=404
                )

            if TwoFactorService.verify_2fa_code(user, code):
                auth_login(request, user)
                # Clean session data
                TwoFactorService.clean_session_keys(request.session)

                return JsonResponse(
                    {
                        "status": "success",
                        "message": "Verificación exitosa",
                        "username": user.username,
                    }
                )

            return JsonResponse(
                {"status": "error", "message": "Código inválido"}, status=400
            )

        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "message": "Formato JSON inválido"}, status=400
            )
        except ValidationError as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
        except PermissionDenied as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=403)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
