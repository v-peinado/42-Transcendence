# authentication/api_views.py
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from .serializers import UserSerializer
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
        user = User.objects.filter(username=username).first()
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(username)
        qr.make(fit=True)
        
        img = qr.make_image(fill='black', back_color='white')
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        return HttpResponse(buffer, content_type="image/png")

@method_decorator(csrf_exempt, name='dispatch')
class ValidateQRCodeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        user = User.objects.filter(username=username).first()
        if user:
            auth_login(request, user)
            return Response({"message": "Login successful"}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid QR code"}, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password1')
        user = authenticate(username=username, password=password)
        
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user_id': user.pk,
                'username': user.username,
                "message": "Login successful"
            })
        return Response({"error": "Invalid credentials"}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(APIView):
    def post(self, request):
        auth_logout(request)
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password1 = request.data.get('password1')
        password2 = request.data.get('password2')

        # Validar campos requeridos
        if not all([username, email, password1, password2]):
            return Response({
                "status": "error",
                "code": "missing_fields",
                "message": "Todos los campos son requeridos"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validar contraseñas
        if password1 != password2:
            return Response({
                "status": "error",
                "code": "password_mismatch",
                "message": "Las contraseñas no coinciden"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validar email
        if User.objects.filter(email=email).exists():
            return Response({
                "status": "error",
                "code": "email_exists",
                "message": "El email ya está registrado"
            }, status=status.HTTP_409_CONFLICT)

        # Validar username
        if User.objects.filter(username=username).exists():
            return Response({
                "status": "error",
                "code": "username_exists",
                "message": "El nombre de usuario ya está registrado"
            }, status=status.HTTP_409_CONFLICT)

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1
            )
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "status": "success",
                "code": "user_created",
                "data": {
                    'token': token.key,
                    'user_id': user.pk,
                    'username': user.username
                }
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                "status": "error",
                "code": "creation_failed",
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)