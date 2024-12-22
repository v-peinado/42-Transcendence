from django.views import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from ...services.password_service import PasswordService
import json

@method_decorator(csrf_exempt, name='dispatch')
class PasswordResetAPIView(View):
    """API para solicitar reseteo de contraseña"""
    def post(self, request, *args, **kwargs):
        try:
            # Obtener datos del request
            if hasattr(request, 'data'):
                data = request.data
            else:
                data = json.loads(request.body)
                
            email = data.get('email')
            # Generar token y datos de verificación
            token_data = PasswordService.initiate_password_reset(email)
            
            if token_data:
                return JsonResponse({
                    'status': 'success',
                    'message': 'Se ha enviado un email con instrucciones',
                    'data': {
                        'uidb64': token_data['uid'],
                        'token': token_data['token']
                    }
                })
                
            return JsonResponse({
                'status': 'success',
                'message': 'Si el email existe, recibirás instrucciones'
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
class PasswordResetConfirmAPIView(View):
    def post(self, request, *args, **kwargs):
        """Confirmar reset de contraseña con token (Sin autenticación)"""
        try:
            if hasattr(request, 'data'):
                data = request.data
            else:
                data = json.loads(request.body)

            result = PasswordService.confirm_password_reset(
                data.get('uidb64'),
                data.get('token'),
                data.get('new_password1'),
                data.get('new_password2')
            )
            return JsonResponse({
                'status': 'success',
                'message': 'Contraseña restablecida correctamente'
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
