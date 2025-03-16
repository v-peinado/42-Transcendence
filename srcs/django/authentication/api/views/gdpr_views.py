from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from ...services.gdpr_service import GDPRService
from django.views import View
import logging
import json

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name="dispatch")
class GDPRSettingsAPIView(View):
    def get(self, request, *args, **kwargs):
        """Get user's GDPR settings"""
        try:
            user = request.user
            settings = GDPRService.get_user_settings(user)
            return JsonResponse({"status": "success", "data": settings})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)


@method_decorator(csrf_exempt, name="dispatch")
class ExportPersonalDataAPIView(View):
    def get(self, request, *args, **kwargs):
        """Export user's personal data"""
        try:
            # Verify if is an download request
            if 'download' in kwargs and kwargs['download'] == True:
                return self.download_data(request)
                
            # Get user data
            data = GDPRService.export_user_data(request.user)

            # Check for errors in data response and return error log
            if "error" in data:
                logger.error(f"Error exporting user data: {data['details']}")
                return JsonResponse({"status": "error", "message": data["details"]}, status=400)

            # Generate download URL
            download_url = f"/api/gdpr/export-data/download/"

			# Return data and download URL
            return JsonResponse(
                {"status": "success", "data": data, "download_url": download_url})

        except Exception as e:
            logger.error(f"Error exporting user data: {str(e)}")
            return JsonResponse({"status": "error", "message": str(e)}, status=401)

    def download_data(self, request):
        """Download authenticated user's personal data"""
        try:
            if not request.user.is_authenticated:
                return JsonResponse(
                    {"status": "error", "message": "user is not authenticated"}, status=401)

            data = GDPRService.export_user_data(request.user) # store user data in "data"
            
            # Check for errors in data response and return error log
            if isinstance(data, dict) and "error" in data:
                logger.error(f"Error downloading data: {data.get('details', 'Desconocido')}")
                return JsonResponse({"status": "error", "message": data.get("details", "Error in exportation")}, status=401)
            
            # If there is no data or data is an empty dictionary
            if not data or (isinstance(data, dict) and not data):
                logger.error("No data found to export")
                return JsonResponse({"status": "error", "message": "No data found to export"}, status=404)
            
            # Create a filename for the downloaded file
            filename = f"user_data_{request.user.username}.json"
            
            # Convert data to JSON format
            json_data = json.dumps(data, indent=4, default=str, ensure_ascii=False)
            
            # Create a response with the JSON data
            response = HttpResponse(json_data, content_type="application/json; charset=utf-8")
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            response["Content-Length"] = len(json_data)
            
            logger.info(f"Downloading GDPR data for user {request.user.username}")
            return response
            
        except Exception as e:
            logger.error(f"Error downloading user data: {str(e)}")
            return JsonResponse({"status": "error", "message": str(e)}, status=400)


@method_decorator(csrf_exempt, name="dispatch")
class PrivacyPolicyAPIView(View):
    def get(self, request, *args, **kwargs):
        """Get privacy policy"""
        try:
            policy_data = {
                "data_collection": [
                    "Nombre de usuario",
                    "Dirección de email",
                    "Imagen de perfil (opcional)",
                ],
                "data_usage": [
                    "Gestionar tu cuenta y perfil",
                    "Proporcionar servicios de autenticación",
                    "Enviar notificaciones importantes",
                ],
                "user_rights": [
                    "Derecho de acceso a tus datos",
                    "Derecho a la portabilidad de datos",
                    "Derecho al olvido",
                    "Derecho a la rectificación",
                ],
                "security_measures": [
                    "Autenticación de dos factores (2FA)",
                    "Encriptación de contraseñas",
                    "Conexiones seguras HTTPS",
                ],
            }
            return JsonResponse({"status": "success", "data": policy_data})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
