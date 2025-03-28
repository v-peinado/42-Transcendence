from django.contrib.auth import update_session_auth_hash
from ...services.profile_service import ProfileService
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import JsonResponse
from django.views import View
import json
from django.contrib.auth.mixins import LoginRequiredMixin


@method_decorator(csrf_exempt, name="dispatch")
class EditProfileAPIView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Autentication required"}, status=401)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """View user profile"""
        try:
            profile_data = ProfileService.get_user_profile_data(request.user)
            return JsonResponse(profile_data)
        except ValidationError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except PermissionDenied as e:
            return JsonResponse({"error": str(e)}, status=403)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    def put(self, request, *args, **kwargs):
        """Update basic profile"""
        try:
            data = (
                request.data if hasattr(request, "data") else json.loads(request.body)
            )
            files = request.FILES if hasattr(request, "FILES") else None

            ProfileService.update_profile(user=request.user, data=data, files=files)
            return JsonResponse(
                {"status": "success", "message": "Perfil actualizado correctamente"}
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    def post(self, request, *args, **kwargs):
        """Handle specific changes (password, email, image)"""
        try:
            # Handle profile image
            if request.FILES and "profile_image" in request.FILES:
                ProfileService.update_profile(
                    user=request.user, data={}, files=request.FILES
                )
                return JsonResponse(
                    {"message": "Imagen de perfil actualizada correctamente"}
                )

            data = (
                request.data if hasattr(request, "data") else json.loads(request.body)
            )

            # Password change
            if all(
                data.get(f)
                for f in ["current_password", "new_password1", "new_password2"]
            ):
                if ProfileService.handle_password_change(
                    request.user,
                    data["current_password"],
                    data["new_password1"],
                    data["new_password2"],
                ):
                    update_session_auth_hash(request, request.user)
                    return JsonResponse(
                        {"message": "Contraseña actualizada correctamente"}
                    )

            # Email change
            if "email" in data:
                message = ProfileService.handle_email_change(
                    request.user, data["email"]
                )
                return JsonResponse({"message": message})

            # Restore image
            if data.get("restore_image"):
                message = ProfileService.handle_image_restoration(request.user)
                return JsonResponse({"message": message})

            return JsonResponse({"error": "Operación no válida"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


@method_decorator(csrf_exempt, name="dispatch")
class UserProfileAPIView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Autentication required"}, status=401)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """Get user profile"""
        try:
            profile_data = ProfileService.get_user_profile_data(request.user)
            return JsonResponse(profile_data)
        except ValidationError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except PermissionDenied as e:
            return JsonResponse({"error": str(e)}, status=403)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


@method_decorator(csrf_exempt, name="dispatch")
class DeleteAccountAPIView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Autentication required"}, status=401)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Delete user account"""
        try:
            if hasattr(request, "data"):
                data = request.data
            else:
                data = json.loads(request.body)

            if ProfileService.delete_user_account(
                request.user, data.get("confirm_password")
            ):
                return JsonResponse(
                    {"status": "success", "message": "Cuenta eliminada correctamente"}
                )

        except ValidationError as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
        except PermissionDenied as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=403)
        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "message": "Invalid JSON data"}, status=400
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
