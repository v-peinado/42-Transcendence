from authentication.fortytwo_auth.services.fortytwo_service import FortyTwoAuthService
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import View
from django.http import JsonResponse

# Vistas Web
def fortytwo_login(request):
    """Vista web para login con 42"""
    success, auth_url, error = FortyTwoAuthService.handle_login(request)
    if not success:
        messages.error(request, f'Error: {error}')
        return redirect('login')
    return redirect(auth_url)

def fortytwo_callback(request):
    """Vista web para callback de 42"""
    success, user, message = FortyTwoAuthService.handle_callback(request)
    
    if not success:
        messages.error(request, message)
        return redirect('login')
        
    if message == 'pending_2fa':
        return HttpResponseRedirect(reverse('verify_2fa'))
        
    return redirect('user')

# Vistas API
class FortyTwoAuthAPIView(View):
    """Vista API para login con 42"""
    def get(self, request):
        success, auth_url, error = FortyTwoAuthService.handle_login(request, is_api=True)
        if not success:
            return JsonResponse({'error': error}, status=400)
        return JsonResponse({'auth_url': auth_url})

class FortyTwoCallbackAPIView(View):
    def get(self, request):
        """Vista API para callback de 42"""
        success, user, message = FortyTwoAuthService.handle_callback(request, is_api=True)
        
        if not success:
            return JsonResponse({'error': message}, status=400)
            
        if message == 'pending_2fa':
            return JsonResponse({
                'status': 'pending_2fa',
                'message': 'Por favor, verifica el código enviado a tu email'
            })
            
        return JsonResponse({
            'status': 'success',
            'message': 'Login successful',
            'user': {
                'username': user.username,
                'email': user.email
            }
        })

#########################################################################################################
# from django.shortcuts import redirect
# from django.contrib import messages
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from .services.fortytwo_service import FortyTwoAuthService
# from django.http import HttpResponseRedirect
# from django.urls import reverse

# # Vistas Web
# def fortytwo_login(request):
#     """Vista web para login con 42"""
#     success, auth_url, error = FortyTwoAuthService.handle_login(request)
#     if not success:
#         messages.error(request, f'Error: {error}')
#         return redirect('login')
#     return redirect(auth_url)

# def fortytwo_callback(request):
#     """Vista web para callback de 42"""
#     success, user, message = FortyTwoAuthService.handle_callback(request)
    
#     if not success:
#         messages.error(request, message)
#         return redirect('login')
        
#     if message == 'pending_2fa':
#         return HttpResponseRedirect(reverse('verify_2fa'))
        
#     return redirect('user')

# # Vistas API
# class FortyTwoAuthAPIView(APIView):
#     """Vista API para login con 42"""
#     def get(self, request):
#         success, auth_url, error = FortyTwoAuthService.handle_login(request, is_api=True)
#         if not success:
#             return Response({'error': error}, status=400)
#         return Response({'auth_url': auth_url})

# class FortyTwoCallbackAPIView(APIView):
#     def get(self, request):
#         """Vista API para callback de 42"""
#         success, user, message = FortyTwoAuthService.handle_callback(request, is_api=True)
        
#         if not success:
#             return Response({'error': message}, status=400)
            
#         if message == 'pending_2fa':
#             return Response({
#                 'status': 'pending_2fa',
#                 'message': 'Por favor, verifica el código enviado a tu email'
#             })
            
#         return Response({
#             'status': 'success',
#             'message': 'Login successful',
#             'user': {
#                 'username': user.username,
#                 'email': user.email
#             }
#         })