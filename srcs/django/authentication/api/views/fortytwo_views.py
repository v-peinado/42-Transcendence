from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import login as auth_login
from ...services.fortytwo_service import FortyTwoService
from ...services.two_factor_service import TwoFactorService
from ...serializers.user_serializers import UserSerializer

@method_decorator(csrf_exempt, name='dispatch')
class FortyTwoLoginView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Obtener URL de autenticación de 42"""
        try:
            auth_url = FortyTwoService.get_authorization_url()
            return Response({
                'status': 'success',
                'auth_url': auth_url
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class FortyTwoCallbackView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Procesar callback de 42"""
        try:
            code = request.GET.get('code')
            if not code:
                return Response({
                    'status': 'error',
                    'message': 'No se proporcionó código de autorización'
                }, status=status.HTTP_400_BAD_REQUEST)

            user, created = FortyTwoService.process_callback(code)
            
            # Si el usuario tiene 2FA activado
            if user.two_factor_enabled:
                request.session['pending_user_id'] = user.id
                request.session['user_authenticated'] = True
                request.session['fortytwo_user'] = True
                
                code = TwoFactorService.generate_2fa_code(user.two_factor_secret)
                TwoFactorService.send_2fa_code(user, code)
                
                return Response({
                    'status': 'success',
                    'require_2fa': True,
                    'message': 'Se requiere verificación 2FA'
                }, status=status.HTTP_200_OK)
            
            # Login directo si no tiene 2FA
            auth_login(request, user)
            return Response({
                'status': 'success',
                'message': 'Login exitoso',
                'user': UserSerializer(user).data,
                'is_new_user': created
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)