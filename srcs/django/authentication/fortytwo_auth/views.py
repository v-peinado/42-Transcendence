from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views import View
from ninja.responses import Response
from authentication.fortytwo_auth.services.fortytwo_service import FortyTwoAuthService
from authentication.api.schemas import FortyTwoCallbackRequestSchema




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

class FortyTwoCallbackAPIView(View):
    def get(self, request, data: FortyTwoCallbackRequestSchema) -> Response:
        # Añadir el código al request.GET
        request.GET = request.GET.copy()
        request.GET['code'] = data.code
        if data.state:
            request.GET['state'] = data.state
            
        success, user, message = FortyTwoAuthService.handle_callback(
            request,
            is_api=True
        )
        
        if not success:
            return Response({
                'status': 'error',
                'message': message
            }, status=400)
            
        if message == 'pending_2fa':
            return Response({
                'status': 'success',
                'message': 'Por favor verifica el código 2FA',
                'require_2fa': True
            })
            
        return Response({
            'status': 'success',
            'message': 'Login exitoso',
            'user': {
                'username': user.username,
                'email': user.email
            }
        })
