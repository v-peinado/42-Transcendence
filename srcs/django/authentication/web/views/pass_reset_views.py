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
            token_data = PasswordService.initiate_password_reset(email)
            
            # Si se generó el token correctamente, redirigir
            if token_data:
                messages.info(self.request, "Si eres usuario, revisa tu correo para recuperar tu contraseña")
                return redirect(self.success_url)
            
            # Si no se encontró el email de usuario, mostrar mismo mensaje por seguridad
            messages.info(self.request, "Si eres usuario, revisa tu correo para recuperar tu contraseña")
            return redirect(self.success_url)
            
        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'authentication/password_reset_confirm.html'
    success_url = reverse_lazy('login')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            if self.kwargs.get('token') and self.kwargs.get('uidb64'):
                # Verificar token y obtener usuario
                TokenService.verify_password_reset_token(
                    self.kwargs['uidb64'],
                    self.kwargs['token']
                )
                context['validlink'] = True
            else:
                context['validlink'] = False
        except ValidationError as e:
            context['validlink'] = False
            messages.error(self.request, str(e))
        return context
    
    def form_valid(self, form):
        try:
            # Primero aplicar nuestra lógica personalizada
            result = PasswordService.confirm_password_reset(
                self.kwargs['uidb64'],
                self.kwargs['token'],
                form.cleaned_data['new_password1'],
                form.cleaned_data['new_password2']
            )
            
            if result:
                # Guardar la marca del flujo en la sesión
                self.request.session['password_reset_flow'] = True
                
                # Llamar a la implementación padre después de nuestra lógica
                response = super().form_valid(form)
                
                # Limpiar la marca del flujo
                if 'password_reset_flow' in self.request.session:
                    del self.request.session['password_reset_flow']
                
                messages.success(self.request, "Contraseña actualizada correctamente")
                return response
            
            messages.error(self.request, "Error al actualizar la contraseña")
            return self.form_invalid(form)
            
        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)