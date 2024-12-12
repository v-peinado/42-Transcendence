from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from ...services.two_factor_service import TwoFactorService
from ...services.verify_email_service import EmailVerificationService
import qrcode
import io
from django.http import HttpResponse
from ...models import CustomUser
############################################################################################################

###Métodos ya depurados (buenos)###

@method_decorator(csrf_exempt, name='dispatch')
class VerifyEmailAPIView(APIView):
    def get(self, request, uidb64, token):
        try:
            EmailVerificationService.verify_email(uidb64, token)
            return Response({
                'status': 'success',
                'message': 'Email verificado correctamente'
            })
        except ValueError as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class VerifyEmailChangeAPIView(APIView):
    def get(self, request, uidb64, token):
        try:
            EmailVerificationService.verify_email_change(uidb64, token)
            return Response({
                'status': 'success',
                'message': 'Email actualizado correctamente'
            })
        except ValueError as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=400)

############################################################################################################

### Métodos para organizar ###

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