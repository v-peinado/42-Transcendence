from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views import View
from django.contrib.auth import login as auth_login
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from authentication.fortytwo_auth.services.fortytwo_service import FortyTwoAuthService
from authentication.services.two_factor_service import TwoFactorService
from authentication.models import CustomUser
import json

# Vistas Web
def fortytwo_login(request):
    """Vista web para login con 42"""
    success, auth_url, error = FortyTwoAuthService.handle_login(request)
    if not success:
        messages.error(request, f'Error: {error}')
        return redirect('login')
    return redirect(auth_url)

def fortytwo_callback(request):
    """Vista web para callback de 42"""
    success, user, message = FortyTwoAuthService.handle_callback(request)
    
    if not success:
        messages.error(request, message)
        return redirect('login')
        
    if message == 'pending_2fa':
        return HttpResponseRedirect(reverse('verify_2fa'))
        
    return redirect('user')

# Vistas API
class FortyTwoLoginAPIView(View):
    """Vista API para login con 42"""
    def get(self, request):
        success, auth_url, error = FortyTwoAuthService.handle_login(request, is_api=True)
        if success:
            return JsonResponse({
                'status': 'success',
                'auth_url': auth_url
            })
        return JsonResponse({
            'status': 'error',
            'message': error
        })

@method_decorator(csrf_exempt, name='dispatch')
class FortyTwoCallbackAPIView(View):
    def post(self, request):  # Cambiar de get a post
        try:
            # Obtener el código del body JSON
            data = json.loads(request.body)
            code = data.get('code')
            
            if not code:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Código no proporcionado'
                }, status=400)
                
            success, user, message = FortyTwoAuthService.handle_callback(
                request,
                is_api=True,
                code=code
            )
            
            if not success and message != 'pending_2fa':
                return JsonResponse({
                    'status': 'error',
                    'message': message
                }, status=400)
                
            if message == 'pending_2fa':
                return JsonResponse({
                    'status': 'success',
                    'message': 'Por favor verifica el código 2FA',
                    'require_2fa': True,
                    'username': user.username
                })
                
            return JsonResponse({
                'status': 'success',
                'message': 'Login exitoso',
                'username': user.username
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Formato JSON inválido'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class FortyTwoVerify2FAView(View):
    """Vista para verificar códigos 2FA de usuarios de 42"""
    def post(self, request):
        try:
            data = json.loads(request.body)
            code = data.get('code')
            
            if not code:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Código no proporcionado'
                }, status=400)

            # Verificar que sea un usuario de 42 con verificación pendiente
            user_id = request.session.get('pending_user_id')
            is_fortytwo = request.session.get('fortytwo_user', False)
            
            if not user_id or not is_fortytwo:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No hay verificación 2FA pendiente para usuario de 42'
                }, status=400)

            try:
                user = CustomUser.objects.get(id=user_id)
            except CustomUser.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Usuario no encontrado'
                }, status=404)

            if TwoFactorService.verify_2fa_code(user, code):
                auth_login(request, user)
                # Limpiar datos de sesión
                TwoFactorService.clean_session_keys(request.session)
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Verificación exitosa',
                    'username': user.username
                })
            
            return JsonResponse({
                'status': 'error',
                'message': 'Código inválido'
            }, status=400)

        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Formato JSON inválido'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
