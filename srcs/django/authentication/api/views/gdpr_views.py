from django.views import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from ...services.gdpr_service import GDPRService

@method_decorator(csrf_exempt, name='dispatch')
class GDPRSettingsAPIView(View):
    # Anteriormente: permission_classes = [IsAuthenticated]
    
    def get(self, request):
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
    # Anteriormente: permission_classes = [IsAuthenticated]
    
    def get(self, request):
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
            return JsonResponse({
                'status': 'success',
                'data': policy_data
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class ExportDataAPIView(View):
    # Anteriormente: permission_classes = [IsAuthenticated]
    
    def get(self, request):
        data = GDPRService.export_user_data(request.user)
        return JsonResponse(data)

##########################################################################################################
# from django.utils.decorators import method_decorator
# from django.views.decorators.csrf import csrf_exempt
# from rest_framework import status
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from ...services.gdpr_service import GDPRService

# @method_decorator(csrf_exempt, name='dispatch')
# class GDPRSettingsAPIView(APIView):
#     permission_classes = [IsAuthenticated]
    
#     def get(self, request):
#         """Obtener configuraciones GDPR del usuario"""
#         try:
#             user = request.user
#             settings = GDPRService.get_user_settings(user)
#             return Response({
#                 'status': 'success',
#                 'data': settings
#             }, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({
#                 'status': 'error',
#                 'message': str(e)
#             }, status=status.HTTP_400_BAD_REQUEST)

# @method_decorator(csrf_exempt, name='dispatch')
# class ExportPersonalDataAPIView(APIView):
#     permission_classes = [IsAuthenticated]
    
#     def get(self, request):
#         """Exportar datos personales del usuario"""
#         try:
#             data = GDPRService.export_user_data(request.user)
#             return Response({
#                 'status': 'success',
#                 'data': data
#             }, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({
#                 'status': 'error',
#                 'message': str(e)
#             }, status=status.HTTP_400_BAD_REQUEST)

# @method_decorator(csrf_exempt, name='dispatch')
# class PrivacyPolicyAPIView(APIView):
#     def get(self, request):
#         """Obtener la política de privacidad"""
#         try:
#             policy_data = {
#                 'data_collection': [
#                     'Nombre de usuario',
#                     'Dirección de email',
#                     'Imagen de perfil (opcional)'
#                 ],
#                 'data_usage': [
#                     'Gestionar tu cuenta y perfil',
#                     'Proporcionar servicios de autenticación',
#                     'Enviar notificaciones importantes'
#                 ],
#                 'user_rights': [
#                     'Derecho de acceso a tus datos',
#                     'Derecho a la portabilidad de datos',
#                     'Derecho al olvido',
#                     'Derecho a la rectificación'
#                 ],
#                 'security_measures': [
#                     'Autenticación de dos factores (2FA)',
#                     'Encriptación de contraseñas',
#                     'Conexiones seguras HTTPS'
#                 ]
#             }
#             return Response({
#                 'status': 'success',
#                 'data': policy_data
#             }, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({
#                 'status': 'error',
#                 'message': str(e)
#             }, status=status.HTTP_400_BAD_REQUEST)

# class ExportDataAPIView(APIView):
#     permission_classes = [IsAuthenticated]
    
#     def get(self, request):
#         data = GDPRService.export_user_data(request.user)
#         return Response(data)