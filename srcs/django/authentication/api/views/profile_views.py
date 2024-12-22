from django.views import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.contrib.auth import update_session_auth_hash
from ...services.profile_service import ProfileService
import json

@method_decorator(csrf_exempt, name='dispatch')
class EditProfileAPIView(View):
    def get(self, request, *args, **kwargs):
        """Ver perfil del usuario"""
        try:
            profile_data = ProfileService.get_user_profile_data(request.user)
            return JsonResponse(profile_data)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def put(self, request, *args, **kwargs):
        """Actualizar perfil básico"""
        try:
            data = request.data if hasattr(request, 'data') else json.loads(request.body)
            files = request.FILES if hasattr(request, 'FILES') else None
            
            ProfileService.update_profile(
                user=request.user,
                data=data,
                files=files
            )
            return JsonResponse({
                'status': 'success',
                'message': 'Perfil actualizado correctamente'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

    def post(self, request, *args, **kwargs):
        """Manejar cambios específicos (contraseña, email, imagen)"""
        try:
            # Manejo de imagen de perfil
            if request.FILES and 'profile_image' in request.FILES:
                ProfileService.update_profile(
                    user=request.user,
                    data={},
                    files=request.FILES
                )
                return JsonResponse({
                    'message': 'Imagen de perfil actualizada correctamente'
                })
                
            data = request.data if hasattr(request, 'data') else json.loads(request.body)
            
            # Cambio de contraseña
            if all(data.get(f) for f in ['current_password', 'new_password1', 'new_password2']):
                if ProfileService.handle_password_change(
                    request.user,
                    data['current_password'],
                    data['new_password1'],
                    data['new_password2']
                ):
                    update_session_auth_hash(request, request.user)
                    return JsonResponse({'message': 'Contraseña actualizada correctamente'})

            # Cambio de email
            if 'email' in data:
                message = ProfileService.handle_email_change(request.user, data['email'])
                return JsonResponse({'message': message})

            # Restaurar imagen
            if data.get('restore_image'):
                message = ProfileService.handle_image_restoration(request.user)
                return JsonResponse({'message': message})

            return JsonResponse({'error': 'Operación no válida'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class UserProfileAPIView(View):
    def get(self, request, *args, **kwargs):
        """Obtener perfil de usuario"""
        try:
            profile_data = ProfileService.get_user_profile_data(request.user)
            return JsonResponse(profile_data)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class DeleteAccountAPIView(View):
    def post(self, request, *args, **kwargs):
        """Eliminar cuenta de usuario"""
        try:
            if hasattr(request, 'data'):
                data = request.data
            else:
                data = json.loads(request.body)
                
            if ProfileService.delete_user_account(request.user, data.get('confirm_password')):
                return JsonResponse({
                    'status': 'success',
                    'message': 'Cuenta eliminada correctamente'
                })
                
        except ValidationError as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
