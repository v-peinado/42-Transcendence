from django.core.management.base import BaseCommand
from django.utils import timezone
from authentication.models import CustomUser
from authentication.services.gdpr_service import GDPRService
from datetime import timedelta

class Command(BaseCommand):
    help = 'Test user inactivity cleanup'

    def handle(self, *args, **kwargs):
        # Crear usuario de prueba
        user = CustomUser.objects.create_user(
            username='inactive_test',
            email='inactive@test.com',
            password='test123'
        )
        user.email_verified = True
        user.is_active = True
        user.last_login = timezone.now() - timedelta(seconds=3600)  # 1 hora de inactividad
        user.save()

        self.stdout.write('Created test user')
        
        # Ejecutar limpieza
        GDPRService.cleanup_inactive_users()
        
        self.stdout.write('Cleanup executed')
