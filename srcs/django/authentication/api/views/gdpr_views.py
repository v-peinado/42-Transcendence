from django.views import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from ...services.gdpr_service import GDPRService

@method_decorator(csrf_exempt, name='dispatch')
class GDPRSettingsAPIView(View):
    def get(self, request, *args, **kwargs):
        """Obtener configuraciones GDPR del usuario"""
        try:
            user = request.user
            settings = GDPRService.get_user_settings(user)
            return JsonResponse({
                'status': 'success',
                'data': settings
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class ExportPersonalDataAPIView(View):
    def get(self, request, *args, **kwargs):
        """Exportar datos personales del usuario"""
        try:
            data = GDPRService.export_user_data(request.user)
            return JsonResponse({
                'status': 'success',
                'data': data
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class PrivacyPolicyAPIView(View):
    def get(self, request, *args, **kwargs):
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
            return JsonResponse({
                'status': 'success',
                'data': policy_data
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class ExportDataAPIView(View):
    def get(self, request, *args, **kwargs):
        try:
            data = GDPRService.export_user_data(request.user)
            return JsonResponse({
                'status': 'success',
                'data': data
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
