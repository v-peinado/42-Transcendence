from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils.html import escape
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from ...services.auth_service import AuthenticationService
from ...services.email_service import EmailService
from ...services.token_service import TokenService
from ...serializers.user_serializers import UserSerializer
from ...utils import validate_printable_chars  
from ...services.two_factor_service import TwoFactorService
from ...models import CustomUser

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
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        
        if user and user.email_verified:
            if user.two_factor_enabled:
                code = TwoFactorService.generate_2fa_code(user)
                TwoFactorService.send_2fa_code(user, code)
                return Response({
                    'status': 'pending_2fa',
                    'message': 'Código 2FA enviado'
                })
            auth_login(request, user)
            return Response({'status': 'success'})
        return Response({'status': 'error'}, status=400)

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
            # Sanitizar datos antes de procesarlos (XSS)
            username = escape(request.data.get('username', ''))
            email = escape(request.data.get('email', ''))
            password = request.data.get('password1')
            
            # Añadir validaciones de caracteres
            if not validate_printable_chars(username):
                return Response({
                    'status': 'error',
                    'message': 'El nombre de usuario no puede contener espacios ni caracteres especiales'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user = AuthenticationService.register_user(
                username=username,
                email=email,
                password=password
            )
            
            token = TokenService.generate_verification_token(user)
            EmailService.send_verification_email(user, token)
            
            return Response({
                'status': 'success',
                'message': 'Te hemos enviado un email para verificar tu cuenta',
                'data': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class GenerateQRAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, username):
        # Código para generar QR
        pass

@method_decorator(csrf_exempt, name='dispatch')
class ValidateQRAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Código para validar QR
        pass

@method_decorator(csrf_exempt, name='dispatch')
class VerifyEmailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try:
            result = AuthenticationService.verify_email(uidb64, token)
            return Response({
                'status': 'success',
                'message': 'Email verificado correctamente'
            }, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)