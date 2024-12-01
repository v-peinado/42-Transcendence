from django.urls import path
from ..views.profile_views import (
    ProfileAPIView,
    ProfileImageAPIView,
    DeleteAccountView
)

urlpatterns = [
    path('profile/', ProfileAPIView.as_view(), name='api_profile'),
    path('image/', ProfileImageAPIView.as_view(), name='api_profile_image'),
    path('delete-account/', DeleteAccountView.as_view(), name='api_delete_account'),
	path('edit/', ProfileAPIView.as_view(), name='api_edit_profile'),
]