from django.urls import path
from . import views

app_name = 'fortytwo_auth' 

urlpatterns = [
    path('42/login/', views.fortytwo_login, name='login'),
    path('42/callback/', views.fortytwo_callback, name='ft_callback'),
    path('api/42/login/', views.FortyTwoAuthAPIView.as_view(), name='api_ft_login'),
    path('api/42/callback/', views.FortyTwoCallbackAPIView.as_view(), name='api_ft_callback'),
]