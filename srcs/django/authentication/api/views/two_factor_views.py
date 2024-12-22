from django.views import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login as auth_login
from ...services.two_factor_service import TwoFactorService
import json

@method_decorator(csrf_exempt, name='dispatch')
class Enable2FAView(View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'error': 'No autorizado'
            }, status=401)
        
        try:
            TwoFactorService.enable_2fa(request.user)
            return JsonResponse({
                'message': '2FA activado correctamente'
            })
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class Verify2FAAPIView(View):
    def post(self, request, *args, **kwargs):
        is_valid, user = TwoFactorService.verify_session(
            request.session.get('pending_user_id'),
            request.session.get('user_authenticated', False)
        )

        if not is_valid:
            return JsonResponse({
                'error': 'Sesión inválida'
            }, status=401)

        try:
            if hasattr(request, 'data'):
                data = request.data
            else:
                data = json.loads(request.body)

            code = data.get('code')
            if TwoFactorService.verify_2fa_code(user, code):
                TwoFactorService.clean_session_keys(request.session)
                # Añadir estas líneas
                auth_login(request, user)
                return JsonResponse({
                    'status': 'success',
                    'message': 'Código verificado correctamente',
                    'redirect_url': '/user/'
                })

            return JsonResponse({
                'error': 'Código inválido'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class Disable2FAView(View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'error': 'No autorizado'
            }, status=401)
            
        try:
            TwoFactorService.disable_2fa(request.user)
            return JsonResponse({
                'message': '2FA desactivado correctamente'
            })
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=400)
