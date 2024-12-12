from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import check_password 
from ...services.profile_service import ProfileService
from ...services.gdpr_service import GDPRService
from ...services.token_service import TokenService
from ...services.verify_email_service import EmailService
from ...services.password_service import PasswordService
from ...models import CustomUser, PreviousPassword
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import re 
from django.http import HttpResponse

@login_required
def edit_profile(request):
    """Editar perfil de usuario"""
    if request.method == 'POST':
        try:
            user = request.user
            
            # Manejar restauración de imágenes
            if user.is_fortytwo_user and 'restore_42_image' in request.POST:
                ProfileService.restore_default_image(user)
                messages.success(request, 'Imagen de perfil restaurada a la imagen de 42')
                return redirect('edit_profile')

            if not user.is_fortytwo_user and 'restore_default_image' in request.POST:
                ProfileService.restore_default_image(user)
                messages.success(request, 'Imagen de perfil restaurada a la imagen por defecto')
                return redirect('edit_profile')

            # Si es usuario manual y hay cambio de email
            if not user.is_fortytwo_user:
                new_email = request.POST.get('email')
                if new_email and new_email != user.email:
                    # Validar que no sea email de 42
                    if re.match(r'.*@student\.42.*\.com$', new_email.lower()):
                        raise ValidationError('Los correos con dominio @student.42*.com están reservados para usuarios de 42')
                        
                    # Validar que el email no esté en uso
                    if CustomUser.objects.exclude(id=user.id).filter(email=new_email).exists():
                        raise ValidationError('Este email ya está en uso')

                    # Generar token de verificación
                    token_data = TokenService.generate_email_verification_token(user)
                    user.pending_email = new_email
                    user.pending_email_token = token_data['token']  # Guardar solo el token
                    user.save()

                    # Preparar datos para el email
                    verification_data = {
                        'uid': token_data['uid'],
                        'token': token_data['token'],
                        'new_email': new_email,
                        'verification_url': f"{settings.SITE_URL}/verify-email-change/{token_data['uid']}/{token_data['token']}/"
                    }

                    # Enviar email de verificación usando EmailService
                    EmailService.send_email_change_verification(user, verification_data)

                    messages.success(request, f'Te hemos enviado un email a {new_email} para confirmar el cambio')
                    return redirect('edit_profile')

            # Manejar cambio de contraseña
            current_password = request.POST.get('current_password')
            new_password1 = request.POST.get('new_password1')
            new_password2 = request.POST.get('new_password2')
            
            if current_password and new_password1 and new_password2:
                # Validar cambio de contraseña
                PasswordService.validate_password_change(
                    request.user,
                    current_password,
                    new_password1,
                    new_password2
                )
                
                # Cambiar contraseña si pasa validación
                request.user.set_password(new_password1)
                request.user.save()
                
                # Guardar historial
                PreviousPassword.objects.create(
                    user=request.user,
                    password=request.user.password
                )
                
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Contraseña actualizada correctamente')
                return redirect('user')
                    
            # Actualizar perfil usando el servicio
            ProfileService.update_profile(
                user=request.user,
                data=request.POST,
                files=request.FILES
            )
            messages.success(request, 'Perfil actualizado correctamente')
            return redirect('user')
        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('edit_profile')
        except Exception as e:
            messages.error(request, str(e))
            
    return render(request, 'authentication/edit_profile.html')

@login_required
def user(request):
    """Perfil de usuario"""
    show_qr = request.user.email_verified
    context = {
        'user': request.user,
        'show_qr': show_qr
    }
    return render(request, 'authentication/user.html', context)

@login_required
def delete_account(request):
    """Eliminar cuenta de usuario"""
    try:
        if request.method == 'POST':
            user = request.user
            
            # Para usuarios no-42, verificar contraseña
            if not user.is_fortytwo_user:
                password = request.POST.get('confirm_password')
                if not user.check_password(password):
                    messages.error(request, 'Contraseña incorrecta')
                    return redirect('edit_profile')
            
            # Anonimizar y eliminar cuenta
            GDPRService.delete_user_data(user)
            messages.success(request, 'Tu cuenta ha sido eliminada')
            return redirect('home')
            
    except Exception as e:
        messages.error(request, str(e))
    
    return redirect('edit_profile')
