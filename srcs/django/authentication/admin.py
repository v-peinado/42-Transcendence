from django.contrib import admin
from django.utils.html import format_html
from django.core.exceptions import ValidationError
from .models import CustomUser, PreviousPassword

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    # Campos mostrados en la lista
    list_display = (
        'username', 
        'email', 
        'is_active', 
        'email_verified', 
        'is_fortytwo_user',
        'display_profile_image',
        'last_login'
    )
    
    # Campos de búsqueda
    search_fields = ('username', 'email', 'fortytwo_id')
    
    # Filtros laterales
    list_filter = (
        'is_active', 
        'email_verified', 
        'is_fortytwo_user', 
        'two_factor_enabled',
        'date_joined',
        'last_login'
    )
    
    # Campos de solo lectura
    readonly_fields = (
        'last_login', 
        'date_joined', 
        'fortytwo_id',
        'email_verification_token',
        'last_2fa_time'
    )
    
    # Ordenamiento por defecto
    ordering = ('-date_joined',)
    
    # Número de items por página
    list_per_page = 25
    
    # Acciones personalizadas
    actions = ['activate_users', 'deactivate_users']
    
    # Optimización de consultas
    list_select_related = True
    
    fieldsets = (
        ('Información básica', {
            'fields': ('username', 'email', 'password'),
            'classes': ('wide',)
        }),
        ('Estado de la cuenta', {
            'fields': ('is_active', 'email_verified', 'is_fortytwo_user'),
            'classes': ('collapse',)
        }),
        ('Seguridad', {
            'fields': ('two_factor_enabled', 'two_factor_secret', 'last_2fa_code', 'last_2fa_time'),
            'classes': ('collapse',)
        }),
        ('Permisos', {
            'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Información adicional', {
            'fields': ('profile_image', 'fortytwo_id', 'fortytwo_image'),
            'classes': ('collapse',)
        }),
        ('Fechas importantes', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )

    def display_profile_image(self, obj):
        if obj.profile_image:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%;" />', 
                             obj.get_profile_image_url())
        return "Sin imagen"
    display_profile_image.short_description = 'Imagen de perfil'

    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
    activate_users.short_description = "Activar usuarios seleccionados"

    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_users.short_description = "Desactivar usuarios seleccionados"

    def save_model(self, request, obj, form, change):
        try:
            super().save_model(request, obj, form, change)
        except ValidationError as e:
            self.message_user(request, f"Error al guardar: {e}", level='ERROR')

@admin.register(PreviousPassword)
class PreviousPasswordAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('user', 'password', 'created_at')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
    list_per_page = 25

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

# Para acceder al panel de administración:
# http://localhost:8000/admin/
#
# Para crear un superusuario:
# docker-compose exec web python manage.py createsuperuser
# 
# Desde la carpeta donde esta docker-compose.yml (srcs)
# Y seguir las instrucciones
#
