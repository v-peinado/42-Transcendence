from django.core.exceptions import ValidationError
from .models import CustomUser, PreviousPassword
from django.utils.html import format_html
from django.contrib import admin

# This file is used to customize the Django admin panel
# It is used to display the models in a more user-friendly way
# and to add some custom actions like activating or deactivating users

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    # Fields shown in the list view
    list_display = (
        "username",
        "email",
        "is_active",
        "email_verified",
        "is_fortytwo_user",
        "display_profile_image",
        "last_login",
    )

    # Search fields
    search_fields = ("username", "email", "fortytwo_id")

    # Side filters
    list_filter = (
        "is_active",
        "email_verified",
        "is_fortytwo_user",
        "two_factor_enabled",
        "date_joined",
        "last_login",
    )

    # Read-only fields
    readonly_fields = (
        "last_login",
        "date_joined",
        "fortytwo_id",
        "email_verification_token",
        "last_2fa_time",
    )

    # Default ordering
    ordering = ("-date_joined",)

    # Items per page
    list_per_page = 25

    # Custom actions
    actions = ["activate_users", "deactivate_users"]

    # Query optimization
    list_select_related = True

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("username", "email", "password"), "classes": ("wide",)},
        ),
        (
            "Account Status",
            {
                "fields": ("is_active", "email_verified", "is_fortytwo_user"),
                "classes": ("collapse",),
            },
        ),
        (
            "Security",
            {
                "fields": (
                    "two_factor_enabled",
                    "two_factor_secret",
                    "last_2fa_code",
                    "last_2fa_time",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Permissions",
            {
                "fields": ("is_staff", "is_superuser", "groups", "user_permissions"),
                "classes": ("collapse",),
            },
        ),
        (
            "Additional Information",
            {
                "fields": ("profile_image", "fortytwo_id", "fortytwo_image"),
                "classes": ("collapse",),
            },
        ),
        (
            "Important Dates",
            {"fields": ("last_login", "date_joined"), "classes": ("collapse",)},
        ),
    )

    def display_profile_image(self, obj):
        if obj.profile_image:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%;" />',
                obj.get_profile_image_url(),
            )
        return "No image"

    display_profile_image.short_description = "Profile Image"

    def activate_users(self, request, queryset):
        queryset.update(is_active=True)

    activate_users.short_description = "Activate selected users"

    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)

    deactivate_users.short_description = "Deactivate selected users"

    def save_model(self, request, obj, form, change):
        try:
            super().save_model(request, obj, form, change)
        except ValidationError as e:
            self.message_user(request, f"Error saving: {e}", level="ERROR")


@admin.register(PreviousPassword)
class PreviousPasswordAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("user", "password", "created_at")
    list_filter = ("created_at",)
    ordering = ("-created_at",)
    list_per_page = 25

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# To access the admin panel:
# http://localhost:8000/admin/
#
# To create a superuser:
# docker-compose exec web python manage.py createsuperuser
#
# From the folder where docker-compose.yml is located (srcs)
# And follow the instructions
#
