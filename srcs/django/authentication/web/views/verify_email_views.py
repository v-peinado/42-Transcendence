from django.shortcuts import redirect
from django.contrib import messages
from ...services.mail_service import EmailVerificationService

def verify_email(request, uidb64, token):
    """Vista para verificación de email"""
    try:
        EmailVerificationService.verify_email(uidb64, token)
        messages.success(request, "Tu cuenta ha sido verificada correctamente.")
    except ValueError as e:
        messages.error(request, str(e))
    return redirect('login')

def verify_email_change(request, uidb64, token):
    """Vista para verificación de cambio de email"""
    try:
        EmailVerificationService.verify_email_change(uidb64, token)
        messages.success(request, 'Tu email ha sido actualizado correctamente')
    except ValueError as e:
        messages.error(request, str(e))
    return redirect('edit_profile')
