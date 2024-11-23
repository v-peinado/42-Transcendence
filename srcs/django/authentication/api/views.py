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
from django.contrib import messages
from django.shortcuts import redirect
from django.core.exceptions import ValidationError
import re
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from .utils import generate_jwt_token, decode_jwt_token

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
            "message": "Logout exitoso"
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
                # Crear usuario pero no activarlo
                user = serializer.save(is_active=False)
                
                # Generar token
                token = generate_jwt_token(user)
                user.email_verification_token = token
                user.save()
                
                # Preparar email
                subject = 'Verifica tu cuenta de PongOrama'
                message = render_to_string('authentication/email_verification.html', {
                    'user': user,
                    'domain': settings.SITE_URL,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': token,
                    'protocol': 'https'
                })
                
                # Enviar email
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                
                # Email de verificación
                subject_verification = 'Verifica tu cuenta de PongOrama'
                message_verification = render_to_string('authentication/email_verification.html', {
                    'user': user,
                    'domain': settings.SITE_URL,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': token,
                    'protocol': 'https'
                })
                
                # Email de bienvenida
                subject_welcome = '¡Bienvenido a PongOrama!'
                message_welcome = render_to_string('authentication/welcome_email.html', {
                    'user': user,
                })
                
                # Enviar ambos emails
                send_mail(subject_verification, message_verification, 
                         settings.DEFAULT_FROM_EMAIL, [user.email])
                send_mail(subject_welcome, message_welcome,
                         settings.DEFAULT_FROM_EMAIL, [user.email])
                
                return Response({
                    "status": "success",
                    "message": "Te hemos enviado un email para verificar tu cuenta",
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

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password1')
        confirm_password = request.POST.get('password2')

        # Validaciones existentes...
        
        try:
            # Crear usuario pero no activarlo
            user = CustomUser.objects.create_user(
                username=username.lower(),
                email=email.lower(),
                password=password,
                is_fortytwo_user=False,
                is_active=False  # Usuario inactivo hasta verificar email
            )
            
            # Generar token JWT
            token = generate_jwt_token(user)
            
            # Preparar email
            subject = 'Verifica tu cuenta de PongOrama'
            message = render_to_string('authentication/email_verification.html', {
                'user': user,
                'domain': settings.SITE_URL,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': token,
                'protocol': 'https'
            })
            
            # Enviar email
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
            messages.success(request, "Te hemos enviado un email para verificar tu cuenta")
            return redirect('login')
        except Exception as e:
            messages.error(request, str(e))
            return redirect('register')

    return render(request, 'authentication/register.html')

def verify_email(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = CustomUser.objects.get(pk=uid)
        
        # Decodificar el token JWT
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        
        if user and payload['user_id'] == user.id:
            user.email_verified = True
            user.is_active = True
            user.save()
            messages.success(request, "Tu cuenta ha sido verificada correctamente, ahora puedes iniciar sesión")
            return redirect('login')
        else:
            messages.error(request, "El enlace de verificación no es válido")
            return redirect('login')
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        messages.error(request, "El enlace de verificación no es válido")
        return redirect('login')

@method_decorator(csrf_exempt, name='dispatch')
class EditProfileView(APIView):
    def post(self, request):
        user = request.user
        
        # Manejar la restauración de la imagen de 42
        if user.is_fortytwo_user and 'restore_42_image' in request.data:
            ander.profile_image = None
            user.save()
            return Response({
                "status": "success",
                "message": "Imagen de perfil restaurada a la imagen de 42"
            }, status=status.HTTP_200_OK)
            
        # Manejar cambio de imagen normal
        if 'profile_image' in request.FILES:
            user.profile_image = request.FILES['profile_image']
            
        # Para usuarios normales, permitir cambios excepto username
        if not user.is_fortytwo_user:
            email = request.data.get('email')
            
            # Validar que el email no sea de 42
            if email and email != user.email:
                if re.match(r'.*@student\.42.*\.com$', email.lower()):
                    return Response({
                        "status": "error",
                        "message": "Los correos con dominio @student.42*.com están reservados para usuarios de 42"
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
                if CustomUser.objects.exclude(id=user.id).filter(email=email).exists():
                    return Response({
                        "status": "error",
                        "message": "Este email ya está en uso"
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
                user.email = email
            
            # Validar y actualizar contraseña si se proporcionó
            current_password = request.data.get('current_password')
            new_password1 = request.data.get('new_password1')
            new_password2 = request.data.get('new_password2')
            
            if current_password and new_password1 and new_password2:
                if not user.check_password(current_password):
                    return Response({
                        "status": "error",
                        "message": "La contraseña actual es incorrecta"
                    }, status=status.HTTP_400_BAD_REQUEST)
                if new_password1 != new_password2:
                    return Response({
                        "status": "error",
                        "message": "Las nuevas contraseñas no coinciden"
                    }, status=status.HTTP_400_BAD_REQUEST)
                user.set_password(new_password1)
                update_session_auth_hash(request, user)
        
        try:
            user.save()
            return Response({
                "status": "success",
                "message": "Perfil actualizado correctamente"
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class DeleteAccountView(APIView):
    def post(self, request):
        user = request.user
        password = request.data.get('confirm_password')

        # Si es un usuario de 42, permitir la eliminación sin contraseña
        if user.is_fortytwo_user:
            user.delete()
            auth_logout(request)
            return Response({
                "status": "success",
                "message": "Tu cuenta ha sido eliminada correctamente"
            }, status=status.HTTP_200_OK)
        # Para usuarios normales, verificar la contraseña
        else:
            if user.check_password(password):
                user.delete()
                auth_logout(request)
                return Response({
                    "status": "success",
                    "message": "Tu cuenta ha sido eliminada correctamente"
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "status": "error",
                    "message": "Contraseña incorrecta"
                }, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        users = CustomUser.objects.filter(email=email, is_active=True)
        if not users.exists():
            return Response({"status": "error", "message": "No existe una cuenta con este correo electrónico."}, status=status.HTTP_404_NOT_FOUND)
        
        user = users.first()
        token = generate_jwt_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_url = f"{settings.SITE_URL}/reset/{uid}/{token}/"
        
        email_body = render_to_string('authentication/password_reset_email.html', {
            'user': user,
            'reset_url': reset_url,
            'domain': settings.SITE_URL,
        })
        send_mail(
            'Recuperación de contraseña',
            email_body,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        return Response({"status": "success", "message": "Se ha enviado un correo con instrucciones para restablecer tu contraseña."})

@method_decorator(csrf_exempt, name='dispatch')
class PasswordResetConfirmView(APIView):
    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=uid)
            payload = decode_jwt_token(token)
            
            if payload and payload['user_id'] == user.id:
                password = request.data.get('password')
                user.set_password(password)
                user.save()
                return Response({"status": "success", "message": "Contraseña actualizada correctamente"})
            else:
                return Response({"status": "error", "message": "El enlace de verificación no es válido"}, status=status.HTTP_400_BAD_REQUEST)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            return Response({"status": "error", "message": "El enlace de verificación no es válido"}, status=status.HTTP_400_BAD_REQUEST)