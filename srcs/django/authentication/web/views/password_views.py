import re
from django.utils.html import strip_tags
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from ...models import CustomUser  # Cambiar la importación

class CustomPasswordResetView(PasswordResetView):
    success_url = reverse_lazy('password_reset_done')
    email_template_name = 'authentication/password_reset_email.html'
    template_name = 'authentication/password_reset.html'

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        
        # Verificar si es un email de 42
        if re.match(r'.*@student\.42.*\.com$', email.lower()):
            messages.error(
                self.request, 
                "Los usuarios de 42 deben iniciar sesión a través del botón de login de 42."
            )
            return self.form_invalid(form)
        
        # Verificar si existe el usuario
        users = CustomUser.objects.filter(
            email__iexact=email,
            is_active=True,
            is_fortytwo_user=False
        )
        
        if not list(users):
            messages.error(self.request, "No existe una cuenta con este correo electrónico.")
            return self.form_invalid(form)
            
        if users.first().is_fortytwo_user:
            messages.error(self.request, "Los usuarios de 42 no pueden usar esta función.")
            return self.form_invalid(form)

        return super().form_valid(form)

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    def form_valid(self, form):
        self.request.session['password_reset_flow'] = True
        response = super().form_valid(form)
        user = form.user
        
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
        
        # Limpiar la marca del flujo
        if 'password_reset_flow' in self.request.session:
            del self.request.session['password_reset_flow']
            
        messages.success(self.request, "Tu contraseña ha sido actualizada correctamente")
        return response