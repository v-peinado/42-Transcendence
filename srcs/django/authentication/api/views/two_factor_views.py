from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from ...services.two_factor_service import TwoFactorService
import json

@csrf_exempt
@require_http_methods(["POST"])
def Enable2FAView(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            'error': 'No autorizado'
        }, status=401)
    
    try:
        TwoFactorService.enable_2fa(request.user)
        return JsonResponse({
            'message': '2FA activado correctamente'
        })
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def Verify2FAAPIView(request):
    is_valid, user = TwoFactorService.verify_session(
        request.session.get('pending_user_id'),
        request.session.get('user_authenticated', False)
    )

    if not is_valid:
        return JsonResponse({
            'error': 'Sesión inválida'
        }, status=401)

    try:
        # Obtener datos ya sea de ninja o del request body
        if hasattr(request, 'data'):
            data = request.data
        else:
            data = json.loads(request.body)

        code = data.get('code')
        if TwoFactorService.verify_2fa_code(user, code):
            TwoFactorService.clean_session_keys(request.session)
            return JsonResponse({
                'message': 'Código verificado correctamente'
            })

        return JsonResponse({
            'error': 'Código inválido'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def Disable2FAView(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            'error': 'No autorizado'
        }, status=401)
        
    try:
        TwoFactorService.disable_2fa(request.user)
        return JsonResponse({
            'message': '2FA desactivado correctamente'
        })
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)

		
##########################################################################################################
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from rest_framework import status
# from ...services.two_factor_service import TwoFactorService

# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def Enable2FAView(request):
#     try:
#         TwoFactorService.enable_2fa(request.user)
#         return Response({
#             'message': '2FA activado correctamente'
#         }, status=status.HTTP_200_OK)
#     except Exception as e:
#         return Response({
#             'error': str(e)
#         }, status=status.HTTP_400_BAD_REQUEST)

# @api_view(['POST'])
# def Verify2FAAPIView(request):
#     is_valid, user = TwoFactorService.verify_session(
#         request.session.get('pending_user_id'),
#         request.session.get('user_authenticated', False)
#     )

#     if not is_valid:
#         return Response({
#             'error': 'Sesión inválida'
#         }, status=status.HTTP_401_UNAUTHORIZED)

#     code = request.data.get('code')
#     if TwoFactorService.verify_2fa_code(user, code):
#         TwoFactorService.clean_session_keys(request.session)
#         return Response({
#             'message': 'Código verificado correctamente'
#         }, status=status.HTTP_200_OK)

#     return Response({
#         'error': 'Código inválido'
#     }, status=status.HTTP_400_BAD_REQUEST)

# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def Disable2FAView(request):
#     try:
#         TwoFactorService.disable_2fa(request.user)
#         return Response({
#             'message': '2FA desactivado correctamente'
#         }, status=status.HTTP_200_OK)
#     except Exception as e:
#         return Response({
#             'error': str(e)
#         }, status=status.HTTP_400_BAD_REQUEST)