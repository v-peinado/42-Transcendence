from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib import messages
from ...services.gdpr_service import GDPRService
import json

@login_required
def gdpr_settings(request):
    """Vista para configuración GDPR"""
    return render(request, 'authentication/gdpr_settings.html')

@login_required
def export_personal_data(request):
    """Vista para exportar datos personales"""
    try:
        # Obtener datos del usuario usando el servicio GDPR
        data = GDPRService.export_user_data(request.user)
        
        # Preparar respuesta JSON para descarga
        response = HttpResponse(
            json.dumps(data, indent=4, default=str),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="{request.user.username}_data.json"'
        return response
    except Exception as e:
        messages.error(request, f"Error al exportar datos: {str(e)}")
        return redirect('gdpr_settings')

@login_required
def delete_account_gdpr(request):
    """Vista para eliminar cuenta (GDPR)"""
    try:
        if request.method == 'POST':
            user = request.user
            
            # Para usuarios no-42, verificar contraseña
            if not user.is_fortytwo_user:
                password = request.POST.get('confirm_password')
                if not user.check_password(password):
                    messages.error(request, 'Contraseña incorrecta')
                    return redirect('gdpr_settings')
            
            # Eliminar cuenta usando el servicio GDPR
            GDPRService.delete_user_data(user)
            messages.success(request, 'Tu cuenta ha sido eliminada')
            return redirect('home')
            
    except Exception as e:
        messages.error(request, str(e))
    
    return redirect('gdpr_settings')

def privacy_policy(request):
    """Vista para mostrar política de privacidad"""
    return render(request, 'authentication/privacy_policy.html')