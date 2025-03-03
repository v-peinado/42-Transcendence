from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.core.exceptions import ValidationError
from ...services.profile_service import ProfileService


@method_decorator(csrf_protect, name="dispatch")
class EditProfileView(LoginRequiredMixin, View):
    template_name = "authentication/edit_profile.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        try:
            user = request.user

            # Restore image
            if (
                "restore_42_image" in request.POST
                or "restore_default_image" in request.POST
            ):
                message = ProfileService.handle_image_restoration(user)
                messages.success(request, message)
                return redirect("edit_profile")

            # Email change for manual users
            if not user.is_fortytwo_user:
                new_email = request.POST.get("email")
                if new_email and new_email != user.email:
                    message = ProfileService.handle_email_change(user, new_email)
                    messages.success(request, message)
                    return redirect("edit_profile")

            # Password change
            if all(
                request.POST.get(f)
                for f in ["current_password", "new_password1", "new_password2"]
            ):
                if ProfileService.handle_password_change(
                    user,
                    request.POST["current_password"],
                    request.POST["new_password1"],
                    request.POST["new_password2"],
                ):
                    update_session_auth_hash(request, user)
                    messages.success(request, "Contraseña actualizada correctamente")
                    return redirect("user")

            # Update profile
            ProfileService.update_profile(user, request.POST, request.FILES)
            messages.success(request, "Perfil actualizado correctamente")
            return redirect("user")

        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, str(e))

        return render(request, self.template_name)


@method_decorator(csrf_protect, name="dispatch")
class UserProfileView(LoginRequiredMixin, View):
    template_name = "authentication/user.html"

    def get(self, request):
        context = ProfileService.get_user_profile_data(request.user)
        return render(request, self.template_name, context)


@method_decorator(csrf_protect, name="dispatch")
class DeleteAccountView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            password = request.POST.get("confirm_password")
            if ProfileService.delete_user_account(request.user, password):
                messages.success(request, "Tu cuenta ha sido eliminada")
                return redirect("home")
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, str(e))

        return redirect("edit_profile")
