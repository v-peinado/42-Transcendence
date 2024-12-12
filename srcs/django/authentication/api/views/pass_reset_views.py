from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.core.exceptions import ValidationError
from ...services.password_service import PasswordService
from django.contrib.auth import update_session_auth_hash
from ...services.verify_email_service import EmailService

@method_decorator(csrf_exempt, name='dispatch')
class PasswordChangeAPIView(APIView):
    """
    Endpoint para cambiar la contraseña del usuario autenticado.
    
    POST /api/password/change/
    Body: {
        "current_password": "actual",
        "new_password1": "nueva",
        "new_password2": "nueva"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Cambiar contraseña"""
        try:
            current_password = request.data.get('current_password')
            new_password1 = request.data.get('new_password1')
            new_password2 = request.data.get('new_password2')

            result = PasswordService.change_password(
                request.user,
                current_password,
                new_password1,
                new_password2
            )
            
            # Mantener la sesión activa
            update_session_auth_hash(request, request.user)
            
            # Enviar notificación por email
            EmailService.send_password_changed_notification(request.user, is_reset=False)
            
            return Response({
                'status': 'success',
                'message': 'Contraseña actualizada correctamente'
            }, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class PasswordResetAPIView(APIView):
    """
    Endpoint para solicitar reseteo de contraseña.
    
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
            PasswordService.initiate_password_reset(email)
            
            return Response({
                'status': 'success',
                'message': 'Si el email existe, recibirás instrucciones para resetear tu contraseña'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class PasswordResetConfirmAPIView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Confirmar reset de contraseña"""
        try:
            uidb64 = request.data.get('uidb64')
            token = request.data.get('token')
            new_password1 = request.data.get('new_password1')
            new_password2 = request.data.get('new_password2')

            result = PasswordService.confirm_password_reset(
                uidb64, token, new_password1, new_password2
            )
            
            return Response({
                'status': 'success',
                'message': 'Contraseña restablecida correctamente'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)