from django.apps import AppConfig

class AuthenticationConfig(AppConfig):
    # Configuración de la aplicación:
    # https://docs.djangoproject.com/en/3.1/ref/applications/
    
	# Tipo de auto campo para las primary keys (id)
    # Por defecto es 'django.db.models.AutoField'
    # 'django.db.models.BigAutoField' para soportar más registros en la base de datos
    # aunque no lo necesitaríamos porque el valor por defecto es suficiente
    default_auto_field = 'django.db.models.BigAutoField'
    
    # Nombre de la aplicación
    name = 'authentication'			# Nombre de la carpeta que contiene la aplicación 
    verbose_name = 'Autenticación'  # Nombre que se mostrará en la interfaz de administración (opcional)
    
    def ready(self):				# Método llamado cuando la aplicación está lista para ser usada (opcional)
        """
        Se ejecuta cuando la aplicación está lista
        Útil para:
					- Registrar señales
					- Inicializar servicios
					- Configurar tareas programadas
        """
        pass

