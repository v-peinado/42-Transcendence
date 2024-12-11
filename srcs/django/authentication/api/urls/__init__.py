from django.urls import path, include

app_name = 'auth_api'

urlpatterns = [
    path('', include('authentication.api.urls.auth_urls')),
    path('', include('authentication.api.urls.gdpr_urls')),
    path('', include('authentication.api.urls.password_urls')),
    path('', include('authentication.api.urls.profile_urls')),
    path('', include('authentication.api.urls.verification_urls')),
    path('42/', include('authentication.fortytwo_auth.urls')),
]
