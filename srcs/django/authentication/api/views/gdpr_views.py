from django.views import View
from django.http import JsonResponse, HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from ...services.gdpr_service import GDPRService
import json

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
            # Obtener datos del usuario
            data = GDPRService.export_user_data(request.user)
            
            # Generar URL de descarga
            download_url = f"/api/gdpr/export/download/{request.user.username}"
            
            return JsonResponse({
                'status': 'success',
                'data': data,
                'download_url': download_url
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

    def get_download(self, request):
        """Descargar datos personales del usuario autenticado"""
        try:
            if not request.user.is_authenticated:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Usuario no autenticado'
                }, status=401)
                
            data = GDPRService.export_user_data(request.user)
            response = HttpResponse(
                json.dumps(data, indent=4, default=str),
                content_type='application/json'
            )
            response['Content-Disposition'] = f'attachment; filename="{request.user.username}_data.json"'
            return response
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
