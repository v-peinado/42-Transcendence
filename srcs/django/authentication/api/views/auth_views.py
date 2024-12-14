from django.contrib.auth import logout as auth_logout
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from ...services.auth_service import AuthenticationService
from ...serializers.user_serializers import UserSerializer

@method_decorator(csrf_exempt, name='dispatch')
class LoginAPIView(APIView):
    """
    API endpoint para autenticación de usuarios.
    
    Methods:
        POST: Autenticar usuario
            Params:
                username (str): Nombre de usuario
                password (str): Contraseña
            Returns:
                200: Login exitoso
                400: Credenciales inválidas
                403: Email no verificado
    """
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            redirect_to = AuthenticationService.login_user(
                request,
                request.data.get('username'),
                request.data.get('password'),
                request.data.get('remember', False)
            )
            
            if redirect_to == 'verify_2fa':
                return Response({
                    'status': 'pending_2fa',
                    'message': 'Código 2FA enviado'
                })
                
            return Response({
                'status': 'success',
                'redirect_url': f'/{redirect_to}/'
            })
            
        except ValidationError as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        auth_logout(request)
        return Response({
            'status': 'success',
            'message': 'Logout exitoso'
        }, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            if AuthenticationService.handle_registration(request.data):
                return Response({
                    'status': 'success',
                    'message': 'Te hemos enviado un email para verificar tu cuenta',
                    'data': UserSerializer(request.user).data
                }, status=status.HTTP_201_CREATED)
                
            return Response({
                'status': 'error',
                'message': 'Error en el registro'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except ValidationError as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
