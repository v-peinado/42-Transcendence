from rest_framework.decorators import api_view, permission_classes 
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import login as auth_login
from ...services.qr_service import QRService
from ...services.two_factor_service import TwoFactorService
from django.http import HttpResponse
from ...models import CustomUser

qr_service = QRService()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def GenerateQRAPIView(request, username):
    """Vista API para generar QR"""
    if not request.user.is_authenticated:
        return Response({
            'error': 'No autenticado'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        buffer = qr_service.generate_qr(username)
        return HttpResponse(
            buffer.getvalue(), 
            content_type="image/png",
            headers={'Cache-Control': 'no-store'}
        )
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def ValidateQRAPIView(request):
    """Vista API para validar QR"""
    try:
        username = request.data.get('username')
        
        if not username:
            return Response({
                'success': False,
                'error': 'Código QR inválido'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        user = CustomUser.objects.filter(username=username).first()
        
        if user:
            if not user.email_verified:
                return Response({
                    'success': False,
                    'error': 'Por favor verifica tu email para activar tu cuenta'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            if user.two_factor_enabled:
                # Guardar datos en sesión
                request.session['pending_user_id'] = user.id
                request.session['user_authenticated'] = True
                request.session['manual_user'] = not user.is_fortytwo_user
                request.session['fortytwo_user'] = user.is_fortytwo_user
                
                # Generar y enviar código 2FA
                code = TwoFactorService.generate_2fa_code(user)
                TwoFactorService.send_2fa_code(user, code)
                
                return Response({
                    'success': True,
                    'require_2fa': True,
                    'redirect_url': '/verify-2fa/',
                    'message': 'Código 2FA enviado a tu email'
                })
            
            # Si no tiene 2FA, login directo
            auth_login(request, user)
            return Response({
                'success': True,
                'redirect_url': '/user/'
            })
            
        return Response({
            'success': False,
            'error': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)