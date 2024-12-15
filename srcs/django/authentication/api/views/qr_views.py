from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from ...services.qr_service import QRService
import json

qr_service = QRService()

@csrf_exempt
@require_http_methods(["GET"])
def GenerateQRAPIView(request, username):
    """Vista API para generar QR"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'error',
            'message': 'No autorizado'
        }, status=401)
    
    try:
        buffer = qr_service.generate_qr(username)
        return HttpResponse(
            buffer.getvalue(), 
            content_type="image/png",
            headers={'Cache-Control': 'no-store'}
        )
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def ValidateQRAPIView(request):
    """Vista API para validar QR"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        
        if not username:
            return JsonResponse({
                'success': False,
                'error': 'Código QR inválido'
            }, status=400)
            
        success, message, redirect_url = qr_service.validate_qr_data(username)
        
        if success:
            if redirect_url == '/verify-2fa/':
                return JsonResponse({
                    'success': True,
                    'require_2fa': True,
                    'message': message,
                    'redirect_url': redirect_url
                })
            
            return JsonResponse({
                'success': True,
                'redirect_url': redirect_url
            })
            
        return JsonResponse({
            'success': False,
            'error': message
        }, status=400)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

#########################################################################################################
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated, AllowAny
# from rest_framework.response import Response
# from rest_framework import status
# from django.views.decorators.csrf import csrf_exempt
# from ...services.qr_service import QRService
# from django.http import HttpResponse


# qr_service = QRService()

# @csrf_exempt
# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def GenerateQRAPIView(request, username):
#     """Vista API para generar QR"""
#     if not request.user.is_authenticated:
#         return Response({
#             'status': 'error',
#             'message': 'No autorizado'
#         }, status=status.HTTP_401_UNAUTHORIZED)
    
#     try:
#         buffer = qr_service.generate_qr(username)
#         return HttpResponse(
#             buffer.getvalue(), 
#             content_type="image/png",
#             headers={'Cache-Control': 'no-store'}
#         )
#     except Exception as e:
#         return Response({
#             'status': 'error',
#             'message': str(e)
#         }, status=status.HTTP_400_BAD_REQUEST)

# @csrf_exempt
# @api_view(['POST'])
# @permission_classes([AllowAny])
# def ValidateQRAPIView(request):
#     """Vista API para validar QR"""
#     try:
#         username = request.data.get('username')
        
#         if not username:
#             return Response({
#                 'success': False,
#                 'error': 'Código QR inválido'
#             }, status=status.HTTP_400_BAD_REQUEST)
            
#         success, message, redirect_url = qr_service.validate_qr_data(username)
        
#         if success:
#             if redirect_url == '/verify-2fa/':
#                 return Response({
#                     'success': True,
#                     'require_2fa': True,
#                     'message': message,
#                     'redirect_url': redirect_url
#                 }, status=status.HTTP_200_OK)
            
#             return Response({
#                 'success': True,
#                 'redirect_url': redirect_url
#             }, status=status.HTTP_200_OK)
            
#         return Response({
#             'success': False,
#             'error': message
#         }, status=status.HTTP_400_BAD_REQUEST)
            
#     except Exception as e:
#         return Response({
#             'success': False,
#             'error': str(e)
#         }, status=status.HTTP_400_BAD_REQUEST)