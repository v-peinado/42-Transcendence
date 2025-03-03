from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib import messages
from ...services.gdpr_service import GDPRService
import json


@login_required
def gdpr_settings(request):
    """GDPR settings view"""
    return render(request, "authentication/gdpr_settings.html")


@login_required
def export_personal_data(request):
    """View for exporting personal data"""
    try:
        # Get user data using GDPR service
        data = GDPRService.export_user_data(request.user)

        # Prepare JSON response for download
        response = HttpResponse(
            json.dumps(data, indent=4, default=str), content_type="application/json"
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{request.user.username}_data.json"'
        )
        return response
    except Exception as e:
        messages.error(request, f"Error al exportar datos: {str(e)}")
        return redirect("gdpr_settings")


def privacy_policy(request):
    """View to display privacy policy"""
    return render(request, "authentication/privacy_policy.html")
