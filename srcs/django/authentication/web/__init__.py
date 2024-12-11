from django.urls import path, include

app_name = 'web'

urlpatterns = [
	path('', include('authentication.web.urls'))
    # path('auth/', include(('authentication.api.urls.auth_urls', 'auth_api'), namespace='auth_api')),
    # path('profile/', include('authentication.api.urls.profile_urls')),
    # path('password/', include('authentication.api.urls.password_urls')),
    # path('verify/', include('authentication.api.urls.verification_urls')),
]