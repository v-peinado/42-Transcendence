

from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.exceptions import ValidationError
from authentication.services.password_service import PasswordService
from django.shortcuts import redirect
from authentication.services.token_service import TokenService

class CustomPasswordResetView(PasswordResetView):
    """Resetear contraseña cuando el usuario la olvida (con validación de email)"""
    success_url = reverse_lazy('password_reset_done')
    email_template_name = 'authentication/password_reset_email.html'
    template_name = 'authentication/password_reset.html'

    def form_valid(self, form):
        try:
            email = form.cleaned_data["email"]
            if PasswordService.initiate_password_reset(email):
                return redirect(self.success_url)
            return self.form_invalid(form)
        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
        

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'authentication/password_reset_confirm.html'
    success_url = reverse_lazy('login')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.kwargs.get('token') and self.kwargs.get('uidb64'):
            try:
                TokenService.verify_password_reset_token(
                    self.kwargs['uidb64'],
                    self.kwargs['token']
                )
                context['validlink'] = True
            except ValidationError as e:
                context['validlink'] = False
                messages.error(self.request, str(e))
        return context
    
    def form_valid(self, form):
        try:
            # Validar token y parámetros
            if not self.kwargs.get('uidb64') or not self.kwargs.get('token'):
                messages.error(self.request, "Faltan parámetros en la URL")
                return self.form_invalid(form)

            # Actualizar contraseña usando nuestro servicio
            if PasswordService.confirm_password_reset(
                self.kwargs['uidb64'],
                self.kwargs['token'],
                form.cleaned_data['new_password1'],
                form.cleaned_data['new_password2']
            ):
                messages.success(self.request, "Contraseña actualizada correctamente")
                return redirect(self.success_url)
            
            messages.error(self.request, "Error al actualizar la contraseña")
            return self.form_invalid(form)

        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
			
# from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
# from django.urls import reverse_lazy
# from django.contrib import messages
# from django.core.exceptions import ValidationError
# from authentication.services.password_service import PasswordService
# from django.shortcuts import redirect

# class CustomPasswordResetView(PasswordResetView):
#     """Resetear contraseña cuando el usuario la olvida (con validación de email)"""
#     success_url = reverse_lazy('password_reset_done')					# URL de redirección después de enviar el email
#     email_template_name = 'authentication/password_reset_email.html'	# Plantilla de email
#     template_name = 'authentication/password_reset.html'				# Plantilla de reseteo de contraseña

#     def form_valid(self, form):											# Método para validar el formulario
#         try:
#             email = form.cleaned_data["email"]
#             if PasswordService.initiate_password_reset(email):
#                 return redirect(self.success_url)
#             return self.form_invalid(form)
#         except ValidationError as e:
#             messages.error(self.request, str(e))
#             return self.form_invalid(form)

# class CustomPasswordResetConfirmView(PasswordResetConfirmView):
#     """Vista para confirmar el reset de contraseña"""
#     template_name = 'authentication/password_reset_confirm.html'
#     success_url = reverse_lazy('login')
    
#     def form_valid(self, form):
#         try:
#             # Obtener uidb64 y token de la URL
#             uidb64 = self.kwargs['uidb64']
#             token = self.kwargs['token']
            
#             # Validar token y actualizar contraseña
#             if PasswordService.confirm_password_reset(
#                 uidb64,
#                 token,
#                 form.cleaned_data['new_password1'],
#                 form.cleaned_data['new_password2']
#             ):
#                 messages.success(self.request, "Contraseña actualizada correctamente")
#                 return redirect(self.success_url)
#         except ValidationError as e:
#             messages.error(self.request, str(e))
            
#         return self.form_invalid(form)