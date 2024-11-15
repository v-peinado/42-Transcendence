from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from authentication.models import CustomUser
from ..serializers.user_serializers import UserSerializer
import qrcode
import io
from django.http import HttpResponse
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.authtoken.models import Token

@method_decorator(csrf_exempt, name='dispatch')
class GenerateQRCodeView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, username):
        try:
            user = CustomUser.objects.filter(username=username).first()
            if not user:
                return Response(
                    {"error": "Usuario no encontrado"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Generar QR con datos seguros
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4
            )
            qr.add_data(username)
            qr.make(fit=True)
            
            # Generar imagen
            img = qr.make_image(fill='black', back_color='white')
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            
            return HttpResponse(
                buffer.getvalue(), 
                content_type="image/png"
            )
        except Exception as e:
            return Response(
                {"error": "Error al generar QR"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@method_decorator(csrf_exempt, name='dispatch')
class ValidateQRCodeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            username = request.data.get('username')
            if not username:
                return Response(
                    {"error": "Username requerido"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = CustomUser.objects.filter(username=username).first()
            if not user:
                return Response(
                    {"error": "Usuario no encontrado"}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            auth_login(request, user)
            return Response({
                "success": True,
                "message": "Login exitoso"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "error": "Error en la validación del QR"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({
                "error": "Usuario y contraseña son requeridos"
            }, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)
        if user:
            auth_login(request, user)
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "status": "success",
                "message": "Login exitoso",
                "token": token.key,
                "user": UserSerializer(user).data
            })
        return Response({
            "error": "Credenciales inválidas"
        }, status=status.HTTP_401_UNAUTHORIZED)

@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(APIView):
    def post(self, request):
        auth_logout(request)
        return Response({
            "status": "success",
            "message": "Logout successful"
            }, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        try:
            if CustomUser.objects.filter(username=request.data.get('username')).exists():
                return Response({
                    "status": "error",
                    "message": "El nombre de usuario ya existe"
                }, status=status.HTTP_400_BAD_REQUEST)

            if serializer.is_valid():
                user = serializer.save()
                return Response({
                    "status": "success",
                    "message": "Usuario creado correctamente",
                    "data": UserSerializer(user).data
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                "status": "error",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)