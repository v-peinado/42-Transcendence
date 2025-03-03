from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    # Application configuration:
    # https://docs.djangoproject.com/en/3.1/ref/applications/

    # Type of auto field for primary keys (id)
    # Default is 'django.db.models.AutoField'
    # 'django.db.models.BigAutoField' to support more records in the database
    # although we wouldn't need it because the default value is sufficient
    default_auto_field = "django.db.models.BigAutoField"

    # Application name
    name = "authentication"  # Name of the folder containing the application
    verbose_name = (
        "Authentication"  # Name to be displayed in the admin interface (optional)
    )

    def ready(
        self,
    ):  # Method called when the application is ready to be used (optional)
        """
        Executes when the application is ready
        Useful for:
                    - Registering signals
                    - Initializing services
                    - Configuring scheduled tasks
        """
        pass
