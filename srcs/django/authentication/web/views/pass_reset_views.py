from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.exceptions import ValidationError
from authentication.services.password_service import PasswordService

class CustomPasswordResetView(PasswordResetView):
    """Resetear contraseña cuando el usuario la olvida (con validación de email)"""
    success_url = reverse_lazy('password_reset_done')					# URL de redirección después de enviar el email
    email_template_name = 'authentication/password_reset_email.html'	# Plantilla de email
    template_name = 'authentication/password_reset.html'				# Plantilla de reseteo de contraseña

    def form_valid(self, form):											# Método para validar el formulario
        try:
            email = form.cleaned_data["email"]
            if PasswordService.initiate_password_reset(email):
                return super().form_valid(form)
            return self.form_invalid(form)
        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Confirmar reseteo de contraseña"""
    def form_valid(self, form):											# Método para validar el formulario
        try:
            if PasswordService.confirm_password_reset(
                self.kwargs['uidb64'],
                self.kwargs['token'],
                form.cleaned_data['new_password1'],
                form.cleaned_data['new_password2']
            ):
                messages.success(self.request, "Tu contraseña ha sido actualizada correctamente")
                return super().form_valid(form)
        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)