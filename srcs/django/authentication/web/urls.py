from django.urls import path, include, reverse_lazy
from django.contrib.auth import views as auth_views
from .views import (
    # auth_views
    home,
    login,
    register,
    logout,
    # gdpr_views
    gdpr_settings,
    export_personal_data,
    privacy_policy,
    # pass_reset_views
    CustomPasswordResetView,
    CustomPasswordResetConfirmView,
    # profile_views
    EditProfileView,
    UserProfileView,
    DeleteAccountView,
    # verify_email_views
    verify_email,
    verify_email_change,
    generate_qr,
    validate_qr,
    # two_factor_views
    enable_2fa,
    verify_2fa,
    disable_2fa,
)

# auth_views
auth_patterns = [
    path("login/", login, name="login"),
    path("logout/", logout, name="logout"),
    path("register/", register, name="register"),
    path(
        "auth/42/",
        include("authentication.fortytwo_auth.urls", namespace="web_fortytwo_auth"),
    ),
]

# gdpr_views
gdpr_patterns = [
    path("gdpr-settings/", gdpr_settings, name="gdpr_settings"),
    path("export-data/", export_personal_data, name="export_data"),
    path("privacy-policy/", privacy_policy, name="privacy_policy"),
]

# pass_reset_views
password_patterns = [
    path("reset_password/", CustomPasswordResetView.as_view(), name="password_reset"),
    path(
        "reset/<uidb64>/<token>/",
        CustomPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset_password/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="authentication/password_reset_done.html"
        ),
        name="password_reset_done",
    ),  # este metodo viene del modulo auth_views de django (no es propio)
    path(
        "reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="authentication/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),  # este metodo viene del modulo auth_views de django (no es propio)
]

# profile_views
profile_patterns = [
    path("profile/edit/", EditProfileView.as_view(), name="edit_profile"),
    path("profile/", UserProfileView.as_view(), name="user"),
    path("profile/delete/", DeleteAccountView.as_view(), name="delete_account"),
]

# verify_email_views
verify_email_patterns = [
    path("verify-email/<str:uidb64>/<str:token>/", verify_email, name="verify_email"),
    path(
        "verify-email-change/<str:uidb64>/<token>/",
        verify_email_change,
        name="verify_email_change",
    ),
    path("generate_qr/<str:username>/", generate_qr, name="generate_qr"),
    path("validate_qr/", validate_qr, name="validate_qr"),
]

# two_factor_views
two_factor_patterns = [
    path("enable-2fa/", enable_2fa, name="enable_2fa"),
    path("verify-2fa/", verify_2fa, name="verify_2fa"),
    path("disable-2fa/", disable_2fa, name="disable_2fa"),
]

urlpatterns = [
    path("", home, name="home"),
    *auth_patterns,
    *profile_patterns,
    *password_patterns,
    *gdpr_patterns,
    *verify_email_patterns,
    *two_factor_patterns,
]
