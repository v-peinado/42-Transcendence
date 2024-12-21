from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from ...services.qr_service import QRService
import json
from django.views import View
from django.utils.decorators import method_decorator

qr_service = QRService()

@method_decorator(csrf_exempt, name='dispatch')
class GenerateQRAPIView(View):
    def get(self, request, username=None, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 'error',
                'message': 'No autorizado'
            }, status=401)
        
        try:
            if not username:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Username no proporcionado'
                }, status=400)
                
            buffer = qr_service.generate_qr(username)
            return HttpResponse(
                buffer.getvalue(), 
                content_type="image/png",
                headers={'Cache-Control': 'no-store'}
            )
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def ValidateQRAPIView(request):
    """Vista API para validar QR"""
    try:
        # Obtener datos ya sea de ninja o del request body
        if hasattr(request, 'data'):
            data = request.data
        else:
            data = json.loads(request.body)
            
        username = data.get('username')
        
        if not username:
            return JsonResponse({
                'success': False,
                'error': 'Código QR inválido'
            }, status=400)
            
        success, message, redirect_url = qr_service.validate_qr_data(username)
        
        if success:
            if redirect_url == '/verify-2fa/':
                return JsonResponse({
                    'success': True,
                    'require_2fa': True,
                    'message': message,
                    'redirect_url': redirect_url
                })
            
            return JsonResponse({
                'success': True,
                'redirect_url': redirect_url
            })
            
        return JsonResponse({
            'success': False,
            'error': message
        }, status=400)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
