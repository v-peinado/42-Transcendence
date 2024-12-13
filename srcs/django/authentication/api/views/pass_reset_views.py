from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.core.exceptions import ValidationError
from ...services.password_service import PasswordService

@method_decorator(csrf_exempt, name='dispatch')
class PasswordResetAPIView(APIView):
    """
    Endpoint para solicitar reseteo de contraseña. (Sin autenticación)
    
    POST /api/password/reset/
    Body: {
        "email": "usuario@ejemplo.com"
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Solicitar reset de contraseña"""
        try:
            email = request.data.get('email')
            if PasswordService.initiate_password_reset(email):
                return Response({
                    'status': 'success',
                    'message': 'Si el email existe, recibirás instrucciones para resetear tu contraseña'
                })
            return Response({
                'status': 'success',
                'message': 'Si el email existe, recibirás instrucciones para resetear tu contraseña'
            })
        except ValidationError as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class PasswordResetConfirmAPIView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Confirmar reset de contraseña con token (Sin autenticación)"""
        try:
            result = PasswordService.confirm_password_reset(
                request.data.get('uidb64'),
                request.data.get('token'),
                request.data.get('new_password1'),
                request.data.get('new_password2')
            )
            return Response({
                'status': 'success',
                'message': 'Contraseña restablecida correctamente'
            })
        except ValidationError as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)