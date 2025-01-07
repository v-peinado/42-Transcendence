from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from django.core.exceptions import ValidationError
from authentication.services.auth_service import AuthenticationService

def home(request):
    """Vista principal"""
    return render(request, 'authentication/home.html')

def login(request):
    """Vista de inicio de sesión para usuarios registrados de forma manual"""
    context = {}
    first_time = request.GET.get('first_time', 'false')
    context['first_time'] = first_time == 'true'
    
    if request.method == 'POST':
        try:
            redirect_to = AuthenticationService.login_user(
                request,
                request.POST.get('username'),
                request.POST.get('password'),
                request.POST.get('remember', None)
            )
            return redirect(redirect_to)
        except ValidationError as e:
            messages.error(request, str(e))
            
    return render(request, 'authentication/login.html', context)

def register(request):
    """Vista de registro para nuevos usuarios que se registran manualmente"""
    if request.method == 'POST':
        try:
            result = AuthenticationService.handle_registration(request.POST)
            if isinstance(result, dict) and result.get('success'):
                messages.success(request, AuthenticationService.MESSAGES['email_verification'])
                return redirect('login')
            elif result:
                messages.success(request, AuthenticationService.MESSAGES['email_verification'])
                return redirect('login')
        except ValidationError as e:
            messages.error(request, str(e))
            
    return render(request, 'authentication/register.html')

def logout(request):
    """Vista de cierre de sesión"""
    auth_logout(request)
    return redirect('home')