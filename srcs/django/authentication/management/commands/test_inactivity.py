from django.core.management.base import BaseCommand
from django.utils import timezone
from authentication.models import CustomUser
from authentication.services.gdpr_service import GDPRService
from datetime import timedelta

class Command(BaseCommand):
    help = 'Test user inactivity cleanup'

    def handle(self, *args, **kwargs):
        # Eliminar usuario de prueba si existe
        CustomUser.objects.filter(username='inactive_test').delete()
        
        # Crear usuario de prueba
        user = CustomUser.objects.create_user(
            username='inactive_test',
            email='inactive@test.com',
            password='test123'
        )
        user.email_verified = True
        user.is_active = True
        
        # Simular último login hace 1 hora
        user.last_login = timezone.now() - timedelta(seconds=3600)
        user.save()

        self.stdout.write(self.style.SUCCESS('Created test user'))
        
        # Ejecutar limpieza
        try:
            GDPRService.cleanup_inactive_users()
            self.stdout.write(self.style.SUCCESS('Cleanup executed'))
            
            # Verificar estado del usuario
            try:
                user.refresh_from_db()
                self.stdout.write(
                    f"User status: notified={user.inactivity_notified}, "
                    f"notification_date={user.inactivity_notification_date}, "
                    f"is_active={user.is_active}"
                )
            except CustomUser.DoesNotExist:
                self.stdout.write(self.style.WARNING('User was deleted'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during cleanup: {str(e)}'))

#Steps to test the code:
#1. docker exec -it srcs-web-1 /bin/bash # access the web container
#2. python manage.py test_inactivity # run the test
#3. python manage.py test_inactivity # run the test again
# Este código:

# Elimina el usuario de prueba si existe
# Crea un nuevo usuario de prueba
# Simula inactividad estableciendo last_login
# Ejecuta la limpieza
# Verifica y muestra el estado del usuario después de la limpieza