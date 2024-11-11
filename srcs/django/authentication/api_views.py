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

class GenerateQRCodeView(APIView):
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

class ValidateQRCodeView(APIView):
    def post(self, request):
        username = request.data.get('username')
        user = User.objects.filter(username=username).first()
        if user:
            auth_login(request, user)
            return Response({"message": "Login successful"}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid QR code"}, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]  # Permite acceso sin autenticación
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password1')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return Response({"message": "Login successful"}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    def post(self, request):
        auth_logout(request)
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)