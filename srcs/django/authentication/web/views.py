from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from authentication.models import CustomUser
import qrcode
import io
import json
from django.views.decorators.csrf import csrf_exempt  
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from ..models import CustomUser 
from ..serializers.user_serializers import UserSerializer
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash

# Vista principal
def home(request):
    return render(request, 'authentication/home.html')

# Vista de inicio de sesión
def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('user')
        else:
            messages.error(request, "Usuario o contraseña incorrectos")
            return redirect('login')

    return render(request, 'authentication/login.html')

# Vista de registro
def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password1')
        confirm_password = request.POST.get('password2')

        if password != confirm_password:
            messages.error(request, "Usuario no registrado. Las contraseñas no coinciden")
            return redirect('register')

        try:
            # Validar si el usuario ya existe
            if CustomUser.objects.filter(username=username).exists():
                messages.error(request, "Usuario no registrado. El nombre de usuario ya está en uso")
                return redirect('register')
            
            # Validar si el email ya existe
            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, "Usuario no registrado. El email ya está registrado")
                return redirect('register')
            
            # Crear usuario con imagen por defecto
            user = CustomUser.objects.create_user(
                username=username, 
                email=email, 
                password=password
            )
            # La imagen por defecto se generará automáticamente en el save() del modelo
            messages.success(request, "Usuario creado correctamente. Puedes iniciar sesión ahora.")
            return redirect('login')

        except Exception as e:
            messages.error(request, "Error inesperado al crear el usuario")
            return redirect('register')

    return render(request, 'authentication/register.html')

# Vista para mostrar todos los usuarios
@login_required
def user(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    context = {
        'user': request.user,
        'show_qr': True  # Para controlar la visualización del QR
    }
    return render(request, 'authentication/user.html', context)

# Vista personalizada de logout
@login_required
def custom_logout(request):
    auth_logout(request)
    return redirect('home')

# Función para generar QR
@login_required
def generate_qr(request, username):
    if not request.user.is_authenticated:
        return redirect('login')
    
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(username)
    qr.make(fit=True)
    
    img = qr.make_image(fill='black', back_color='white')
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    
    return HttpResponse(buffer.getvalue(), content_type="image/png")

# Función para validar QR
@csrf_exempt  # Mantener csrf_exempt
def validate_qr(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')  # Cambiar qr_data por username
            
            if not username:
                return JsonResponse({'success': False, 'error': 'Código QR inválido'})
                
            user = CustomUser.objects.filter(username=username).first()
            
            if user:
                auth_login(request, user)
                return JsonResponse({
                    'success': True,
                    'redirect_url': '/user/'  # Añadir URL de redirección
                })
            else:
                return JsonResponse({'success': False, 'error': 'Usuario no encontrado'})
                
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Datos inválidos'})
            
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

# Vistas de API
class UserList(generics.ListCreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password1')  # Actualizado para coincidir
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return Response({"message": "Login successful"}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    def post(self, request):
        auth_logout(request)
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        user = request.user
        
        # Permitir cambiar la imagen de perfil para todos los usuarios
        if 'profile_image' in request.FILES:
            user.profile_image = request.FILES['profile_image']
            user.save()
            messages.success(request, 'Imagen de perfil actualizada correctamente')
            
        # Si es usuario de 42, solo permitir cambiar la imagen
        if user.is_fortytwo_user:
            return redirect('user')
            
        # Para usuarios normales, permitir todos los cambios
        email = request.POST.get('email')
        current_password = request.POST.get('current_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        # Actualizar email
        if email and email != user.email:
            if CustomUser.objects.exclude(id=user.id).filter(email=email).exists():
                messages.error(request, 'Este email ya está en uso')
                return redirect('edit_profile')
            user.email = email
            
        # Actualizar imagen de perfil
        if 'profile_image' in request.FILES:
            user.profile_image = request.FILES['profile_image']
            
        # Actualizar contraseña si se proporcionó
        if current_password and new_password1 and new_password2:
            if not user.check_password(current_password):
                messages.error(request, 'La contraseña actual es incorrecta')
                return redirect('edit_profile')
            if new_password1 != new_password2:
                messages.error(request, 'Las nuevas contraseñas no coinciden')
                return redirect('edit_profile')
            user.set_password(new_password1)
            update_session_auth_hash(request, user)
            
        user.save()
        messages.success(request, 'Perfil actualizado correctamente')
        return redirect('user')
        
    return render(request, 'authentication/edit_profile.html')

@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        password = request.POST.get('confirm_password')

        # Si es un usuario de 42, permitir la eliminación sin contraseña
        if user.is_fortytwo_user:
            user.delete()
            auth_logout(request)
            messages.success(request, 'Tu cuenta ha sido eliminada correctamente')
            return redirect('home')
        # Para usuarios normales, verificar la contraseña
        else:
            if user.check_password(password):
                user.delete()
                auth_logout(request)
                messages.success(request, 'Tu cuenta ha sido eliminada correctamente')
                return redirect('home')
            else:
                messages.error(request, 'Contraseña incorrecta')
                return redirect('edit_profile')

    return redirect('edit_profile')