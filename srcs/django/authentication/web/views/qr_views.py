from django.shortcuts import redirect
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ...models import CustomUser
from ...services.qr_service import QRService
import json

@login_required
def generate_qr(request, username):
    """Vista web para generar QR"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    buffer = QRService.generate_qr(username)
    return HttpResponse(buffer.getvalue(), content_type="image/png")

@csrf_exempt
def validate_qr(request):
    """Vista web para validar QR"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
        
    try:
        data = json.loads(request.body)
        username = data.get('username')
        
        if not username:
            return JsonResponse({'success': False, 'error': 'Código QR inválido'})
            
        user = CustomUser.objects.filter(username=username).first()
        success, message, redirect_url = QRService.validate_qr_data(user)
        
        if success:
            if redirect_url == '/verify-2fa/':
                request.session.update({
                    'pending_user_id': user.id,
                    'user_authenticated': True,
                    'manual_user': not user.is_fortytwo_user,
                    'fortytwo_user': user.is_fortytwo_user
                })
                return JsonResponse({
                    'success': True,
                    'require_2fa': True,
                    'redirect_url': redirect_url,
                    'message': message
                })
            else:
                auth_login(request, user)
                return JsonResponse({
                    'success': True,
                    'redirect_url': redirect_url
                })
                
        return JsonResponse({'success': False, 'error': message})
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Datos inválidos'})