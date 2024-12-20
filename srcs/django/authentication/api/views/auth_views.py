from django.views import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from ...services.auth_service import AuthenticationService
import json
from django.contrib.auth.decorators import login_required

@method_decorator(csrf_exempt, name='dispatch')
class LoginAPIView(View):
    """
    API endpoint para autenticación de usuarios.
    
    Methods:
        POST: Autenticar usuario
            Params:
                username (str): Nombre de usuario
                password (str): Contraseña
            Returns:
                200: Login exitoso
                400: Credenciales inválidas
                403: Email no verificado
    """
    def post(self, request, *args, **kwargs):
        try:
            # Obtener datos ya sea de ninja o del request body
            if hasattr(request, 'data'):
                data = request.data
            else:
                data = json.loads(request.body)

            redirect_to = AuthenticationService.login_user(
                request,
                data.get('username'),
                data.get('password'),
                data.get('remember', False)
            )
            
            if redirect_to == 'verify_2fa':
                return JsonResponse({
                    'status': 'pending_2fa',
                    'message': 'Código 2FA enviado'
                })
                
            return JsonResponse({
                'status': 'success',
                'redirect_url': f'/{redirect_to}/'
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

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class LogoutAPIView(View):
    def post(self, request, *args, **kwargs):
        try:
            AuthenticationService.logout_user(request)
            return JsonResponse({
                'status': 'success',
                'message': AuthenticationService.MESSAGES['logout_success']
            })
        except ValidationError as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class RegisterAPIView(View):
    def post(self, request, *args, **kwargs):
        try:
            # Obtener datos ya sea de ninja o del request body
            if hasattr(request, 'data'):
                data = request.data
            else:
                data = json.loads(request.body)

            try:
                result = AuthenticationService.handle_registration(data)
                
                if isinstance(result, dict):
                    # Si el servicio devuelve un diccionario con datos adicionales
                    return JsonResponse({
                        'status': 'success',
                        'message': AuthenticationService.MESSAGES['email_verification'],
                        'data': result
                    }, status=201)
                elif result:
                    # Si el servicio devuelve True
                    return JsonResponse({
                        'status': 'success',
                        'message': AuthenticationService.MESSAGES['email_verification']
                    }, status=201)
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': AuthenticationService.MESSAGES['form_validation']
                    }, status=400)

            except ValidationError as service_error:
                return JsonResponse({
                    'status': 'error',
                    'message': str(service_error)
                }, status=400)

        except json.JSONDecodeError as json_error:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': AuthenticationService.MESSAGES.get(
                    'unexpected_error', 
                    'Error inesperado en el servidor'
                )
            }, status=500)
