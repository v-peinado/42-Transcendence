from django.urls import path
from ..views.gdpr_views import (
    GDPRSettingsAPIView,
    ExportPersonalDataAPIView,
    PrivacyPolicyAPIView,
    DeleteAccountAPIView
)

urlpatterns = [
    path('gdpr/settings/', GDPRSettingsAPIView.as_view(), name='api_gdpr_settings'),
    path('gdpr/export-data/', ExportPersonalDataAPIView.as_view(), name='api_export_data'),
    path('gdpr/privacy-policy/', PrivacyPolicyAPIView.as_view(), name='api_privacy_policy'),
    path('gdpr/delete-account/', DeleteAccountAPIView.as_view(), name='api_delete_account'),
]