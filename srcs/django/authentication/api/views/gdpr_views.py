from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ...services.gdpr_service import GDPRService

@method_decorator(csrf_exempt, name='dispatch')
class GDPRSettingsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Obtener configuraciones GDPR del usuario"""
        try:
            user = request.user
            settings = GDPRService.get_user_settings(user)
            return Response({
                'status': 'success',
                'data': settings
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class ExportPersonalDataAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Exportar datos personales del usuario"""
        try:
            data = GDPRService.export_user_data(request.user)
            return Response({
                'status': 'success',
                'data': data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class DeleteAccountAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Eliminar cuenta de usuario"""
        try:
            user = request.user
            # Si es usuario manual, verificar contraseña
            if not user.is_fortytwo_user:
                password = request.data.get('confirm_password')
                if not user.check_password(password):
                    return Response({
                        'status': 'error',
                        'message': 'Contraseña incorrecta'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            GDPRService.delete_user_data(user)
            return Response({
                'status': 'success',
                'message': 'Cuenta eliminada correctamente'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class PrivacyPolicyAPIView(APIView):
    def get(self, request):
        """Obtener la política de privacidad"""
        try:
            policy_data = {
                'data_collection': [
                    'Nombre de usuario',
                    'Dirección de email',
                    'Imagen de perfil (opcional)'
                ],
                'data_usage': [
                    'Gestionar tu cuenta y perfil',
                    'Proporcionar servicios de autenticación',
                    'Enviar notificaciones importantes'
                ],
                'user_rights': [
                    'Derecho de acceso a tus datos',
                    'Derecho a la portabilidad de datos',
                    'Derecho al olvido',
                    'Derecho a la rectificación'
                ],
                'security_measures': [
                    'Autenticación de dos factores (2FA)',
                    'Encriptación de contraseñas',
                    'Conexiones seguras HTTPS'
                ]
            }
            return Response({
                'status': 'success',
                'data': policy_data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class ExportDataAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        data = GDPRService.export_user_data(request.user)
        return Response(data)