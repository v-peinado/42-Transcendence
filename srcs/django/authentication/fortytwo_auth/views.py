from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views import View
from ninja.responses import Response
from authentication.fortytwo_auth.services.fortytwo_service import FortyTwoAuthService
from authentication.api.schemas import FortyTwoCallbackRequestSchema
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator




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
            import json
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
            
            if not success:
                return JsonResponse({
                    'status': 'error',
                    'message': message
                }, status=400)
                
            if message == 'pending_2fa':
                return JsonResponse({
                    'status': 'success',
                    'message': 'Por favor verifica el código 2FA',
                    'require_2fa': True
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
