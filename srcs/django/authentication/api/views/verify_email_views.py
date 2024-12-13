from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from ...services.mail_service import EmailVerificationService

@method_decorator(csrf_exempt, name='dispatch')
class VerifyEmailAPIView(APIView):
    def get(self, request, uidb64, token):
        try:
            EmailVerificationService.verify_email(uidb64, token)
            return Response({
                'status': 'success',
                'message': 'Email verificado correctamente'
            })
        except ValueError as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class VerifyEmailChangeAPIView(APIView):
    def get(self, request, uidb64, token):
        try:
            EmailVerificationService.verify_email_change(uidb64, token)
            return Response({
                'status': 'success',
                'message': 'Email actualizado correctamente'
            })
        except ValueError as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=400)
