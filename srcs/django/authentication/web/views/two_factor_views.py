from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseNotAllowed
from ...services.two_factor_service import TwoFactorService
from ...models import CustomUser


@login_required
def enable_2fa(request):
    """Enable 2FA through profile editing"""
    if request.method == "POST":  # If form is submitted
        try:
            TwoFactorService.enable_2fa(request.user)
            messages.success(
                request, "2FA activado correctamente"
            )  # Show success message
            return redirect("user")
        except Exception as e:  # Catch any TwoFactorService exception
            messages.error(request, str(e))
            return redirect("user")
    return render(request, "authentication/enable_2fa.html")


def verify_2fa(request):
    """Verify 2FA when trying to log in"""
    is_valid, user = TwoFactorService.verify_session(
        request.session.get("pending_user_id"),
        request.session.get("user_authenticated", False),
    )

    if not is_valid:
        messages.error(request, "Sesión inválida")
        return redirect("login")

    if request.method == "POST":  # If form is submitted
        code = request.POST.get("code")  # Get 2FA code from form
        if TwoFactorService.verify_2fa_code(user, code):  # If code is valid...
            TwoFactorService.clean_session_keys(request.session)
            auth_login(request, user)
            messages.success(request, "Inicio de sesión exitoso")
            return redirect("user")
        messages.error(request, "Código inválido")

    return render(request, "authentication/verify_2fa.html")


@login_required
def disable_2fa(request):
    """Disable 2FA through profile editing"""
    if request.method == "POST":
        try:
            TwoFactorService.disable_2fa(request.user)
            messages.success(request, "2FA desactivado correctamente")
            return redirect("user")
        except Exception as e:
            messages.error(request, str(e))
            return redirect("user")
    return HttpResponseNotAllowed(["POST"])
