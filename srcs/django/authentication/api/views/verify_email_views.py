from ...services.mail_service import EmailVerificationService
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views import View


@method_decorator(csrf_exempt, name="dispatch")
class VerifyEmailAPIView(View):
    def get(self, request, uidb64, token, *args, **kwargs):
        try:
            EmailVerificationService.verify_email(uidb64, token)
            return JsonResponse(
                {"status": "success", "message": "Email verificado correctamente"}
            )
        except ValueError as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)


@method_decorator(csrf_exempt, name="dispatch")
class VerifyEmailChangeAPIView(View):
    def get(self, request, uidb64, token, *args, **kwargs):
        try:
            EmailVerificationService.verify_email_change(uidb64, token)
            return JsonResponse(
                {"status": "success", "message": "Email actualizado correctamente"}
            )
        except ValueError as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
