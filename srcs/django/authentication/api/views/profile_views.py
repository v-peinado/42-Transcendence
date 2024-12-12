from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from django.contrib.auth import update_session_auth_hash
from ...services.profile_service import ProfileService

@method_decorator(csrf_exempt, name='dispatch')
class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Obtener datos del perfil"""
        try:
            user = request.user
            profile_data = ProfileService.get_profile_data(user)
            return Response(profile_data)
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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

    def put(self, request):
        try:
            user = request.user
            
            # Restaurar imagen
            if request.data.get('restore_image'):
                message = ProfileService.handle_image_restoration(user)
                return Response({'message': message})

            # Cambio de email
            if not user.is_fortytwo_user and request.data.get('email'):
                message = ProfileService.handle_email_change(user, request.data['email'])
                return Response({'message': message})

            # Cambio de contraseña
            if all(request.data.get(f) for f in ['current_password', 'new_password1', 'new_password2']):
                if ProfileService.handle_password_change(
                    user,
                    request.data['current_password'],
                    request.data['new_password1'],
                    request.data['new_password2']
                ):
                    update_session_auth_hash(request, user)
                    return Response({'message': 'Contraseña actualizada correctamente'})

            # Actualizar perfil
            ProfileService.update_profile(user, request.data, request.FILES)
            return Response({'message': 'Perfil actualizado correctamente'})

        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Obtener perfil de usuario"""
        try:
            profile_data = ProfileService.get_user_profile_data(request.user)
            return Response(profile_data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@method_decorator(csrf_exempt, name='dispatch')
class DeleteAccountAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Eliminar cuenta de usuario"""
        try:
            user = request.user
            password = request.data.get('confirm_password')
            
            if ProfileService.delete_user_account(user, password):
                return Response({
                    'status': 'success',
                    'message': 'Cuenta eliminada correctamente'
                }, status=status.HTTP_200_OK)
                
        except ValidationError as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
