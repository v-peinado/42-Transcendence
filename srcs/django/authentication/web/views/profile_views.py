from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.core.exceptions import ValidationError
from ...services.profile_service import ProfileService

@login_required
def edit_profile(request):
    """Vista web para editar perfil"""
    if request.method == 'POST':
        try:
            user = request.user
            
            # Restaurar imagen
            if 'restore_42_image' in request.POST or 'restore_default_image' in request.POST:
                message = ProfileService.handle_image_restoration(user)
                messages.success(request, message)
                return redirect('edit_profile')

            # Cambio de email para usuarios manuales
            if not user.is_fortytwo_user:
                new_email = request.POST.get('email')
                if new_email and new_email != user.email:
                    message = ProfileService.handle_email_change(user, new_email)
                    messages.success(request, message)
                    return redirect('edit_profile')

            # Cambio de contraseña
            if all(request.POST.get(f) for f in ['current_password', 'new_password1', 'new_password2']):
                if ProfileService.handle_password_change(
                    user,
                    request.POST['current_password'],
                    request.POST['new_password1'],
                    request.POST['new_password2']
                ):
                    update_session_auth_hash(request, user)
                    messages.success(request, 'Contraseña actualizada correctamente')
                    return redirect('user')

            # Actualizar perfil
            ProfileService.update_profile(user, request.POST, request.FILES)
            messages.success(request, 'Perfil actualizado correctamente')
            return redirect('user')
            
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, str(e))
            
    return render(request, 'authentication/edit_profile.html')

@login_required
def user(request):
    """Vista web del perfil de usuario"""
    context = ProfileService.get_user_profile_data(request.user)
    return render(request, 'authentication/user.html', context)

@login_required
def delete_account(request):
    """Vista web para eliminar cuenta"""
    try:
        if request.method == 'POST':
            password = request.POST.get('confirm_password')
            if ProfileService.delete_user_account(request.user, password):
                messages.success(request, 'Tu cuenta ha sido eliminada')
                return redirect('home')
    except ValidationError as e:
        messages.error(request, str(e))
    except Exception as e:
        messages.error(request, str(e))
    
    return redirect('edit_profile')
