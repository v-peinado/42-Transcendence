from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from ...services.two_factor_service import TwoFactorService
from ...services.auth_service import AuthenticationService
from django.contrib.auth import login as auth_login
import qrcode
import io
from django.http import HttpResponse
from ...models import CustomUser
from ...services.token_service import TokenService

@method_decorator(csrf_exempt, name='dispatch')
class Enable2FAView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Activar 2FA para un usuario"""
        try:
            code = TwoFactorService.enable_2fa(request.user)
            return Response({
                'status': 'success',
                'message': 'Código 2FA enviado a tu email',
                'data': {'code': code}
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class Verify2FAAPIView(APIView):
    def post(self, request):
        code = request.data.get('code')
        user_id = request.session.get('pending_user_id')
        
        if not user_id:
            return Response({'error': 'No hay verificación pendiente'}, status=400)
            
        user = CustomUser.objects.get(id=user_id)
        if TwoFactorService.verify_2fa_code(user, code):
            auth_login(request, user)
            return Response({'status': 'success'})
        return Response({'error': 'Código inválido'}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class Disable2FAView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Desactivar 2FA para un usuario"""
        try:
            TwoFactorService.disable_2fa(request.user)
            return Response({
                'status': 'success',
                'message': '2FA desactivado correctamente'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class VerifyEmailView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, uidb64, token):
        """Verificar email de usuario"""
        try:
            result = AuthenticationService.verify_email(uidb64, token)
            return Response({
                'status': 'success',
                'message': 'Email verificado correctamente'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class GenerateQRCodeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, username):
        if not request.user.is_authenticated:
            return Response({
                'status': 'error',
                'message': 'No autorizado'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(username)
        qr.make(fit=True)
        
        img = qr.make_image(fill='black', back_color='white')
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        return HttpResponse(buffer.getvalue(), content_type="image/png")

@method_decorator(csrf_exempt, name='dispatch')
class ValidateQRCodeAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        if not username:
            return Response({
                'success': False,
                'error': 'Código QR inválido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = CustomUser.objects.get(username=username)
            if not user.email_verified:
                return Response({
                    'success': False,
                    'error': 'Por favor verifica tu email'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if user.two_factor_enabled:
                code = TwoFactorService.generate_2fa_code(user)
                TwoFactorService.send_2fa_code(user, code)
                return Response({
                    'success': True,
                    'require_2fa': True,
                    'message': 'Código 2FA enviado'
                }, status=status.HTTP_200_OK)
            
            return Response({
                'success': True,
                'redirect_url': '/user/'
            }, status=status.HTTP_200_OK)
            
        except CustomUser.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Usuario no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)