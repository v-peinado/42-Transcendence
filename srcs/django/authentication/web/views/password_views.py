import re
from django.utils.html import strip_tags
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from ...models import CustomUser

class CustomPasswordResetView(PasswordResetView):
    """Resetear contraseña cuando el usuario la olvida (con validación de email)"""
    success_url = reverse_lazy('password_reset_done')					# URL de redirección después de enviar el email
    email_template_name = 'authentication/password_reset_email.html'	# Plantilla de email
    template_name = 'authentication/password_reset.html'				# Plantilla de reseteo de contraseña

    def form_valid(self, form):											# Método para validar el formulario
        email = form.cleaned_data["email"]								# Obtener email del formulario
        
        # Verificar si es un email de 42
        if re.match(r'.*@student\.42.*\.com$', email.lower()):			# Si es un email de 42...
            messages.error(
                self.request, 
                "Los usuarios de 42 deben iniciar sesión a través del botón de login de 42."
            )
            return self.form_invalid(form)
        
        # Verificar si existe el usuario y no es de 42 ni está desactivado
        users = CustomUser.objects.filter(
            email__iexact=email,
            is_active=True,
            is_fortytwo_user=False
        )
	
        if not list(users):												# Si no se encuentra el usuario...
            messages.error(self.request, "No existen usuarios validados con ese email.")
            return self.form_invalid(form)								# Mostrar error y redirigir al formulario
            
        if users.first().is_fortytwo_user:								# Si el usuario es de 42 (no debería pasar pero lo aplico por seguridad)
            messages.error(self.request, "Los usuarios de 42 no pueden usar esta función.")
            return self.form_invalid(form)

        return super().form_valid(form)									# Si todo está bien, continuar con el flujo de reseteo de contraseña

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Confirmar reseteo de contraseña"""
    def form_valid(self, form):											# Método para validar el formulario
        self.request.session['password_reset_flow'] = True				# Agregar marca al flujo de reseteo de contraseña (bloquea mientras se resetea)
        response = super().form_valid(form)								# Continuar con el flujo de reseteo de contraseña
        user = form.user												# Obtener usuario del formulario
        
        # Enviar email de confirmación
        subject = 'Tu contraseña ha sido cambiada'
        html_message = render_to_string('authentication/password_changed_email.html', {
            'user': user,
            'reset': True
        })
        send_mail(
            subject,
            strip_tags(html_message),
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
            html_message=html_message
        )
        
        if 'password_reset_flow' in self.request.session:				# Si el flujo de reseteo de contraseña está en la sesión...
            del self.request.session['password_reset_flow']				# Desbloquear flujo de reseteo de contraseña
            
        messages.success(self.request, "Tu contraseña ha sido actualizada correctamente")
        return response