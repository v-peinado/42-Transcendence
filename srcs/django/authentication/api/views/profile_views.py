from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from ...services.profile_service import ProfileService
from ...services.gdpr_service import GDPRService
from ...serializers.user_serializers import UserSerializer
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from ...services.token_service import TokenService
from ...services.verify_email_service import EmailService

@method_decorator(csrf_exempt, name='dispatch')
class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Obtener perfil del usuario"""
        try:
            serializer = UserSerializer(request.user)
            return Response({
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        """Actualizar perfil del usuario"""
        try:
            ProfileService.update_profile(
                user=request.user,
                data=request.data,
                files=request.FILES
            )
            return Response({
                'status': 'success',
                'message': 'Perfil actualizado correctamente'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        try:
            ProfileService.update_profile(request.user, request.data)
            return Response({'status': 'success'})
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class ProfileImageAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Actualizar imagen de perfil"""
        try:
            if 'profile_image' not in request.FILES:
                return Response({
                    'status': 'error',
                    'message': 'No se proporcionó imagen'
                }, status=status.HTTP_400_BAD_REQUEST)

            ProfileService.update_profile(
                user=request.user,
                data={},
                files=request.FILES
            )
            return Response({
                'status': 'success',
                'message': 'Imagen actualizada correctamente'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Restaurar imagen por defecto"""
        try:
            ProfileService.restore_default_image(request.user)
            return Response({
                'status': 'success',
                'message': 'Imagen restaurada correctamente'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Eliminar cuenta del usuario"""
        try:
            user = request.user
            if not user.is_fortytwo_user:
                password = request.data.get('confirm_password')
                if not user.check_password(password):
                    return Response({
                        'status': 'error',
                        'message': 'Contraseña incorrecta'
                    }, status=status.HTTP_400_BAD_REQUEST)

            GDPRService.delete_user_data(user)
            return Response({
                'status': 'success',
                'message': 'Cuenta eliminada correctamente'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        # Manejar la restauración de imágenes
        if user.is_fortytwo_user and 'restore_42_image' in request.POST:
            user.profile_image = None
            user.save()
            messages.success(request, 'Imagen de perfil restaurada a la imagen de 42')
            return redirect('edit_profile')