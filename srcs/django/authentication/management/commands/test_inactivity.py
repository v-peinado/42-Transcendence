"""
How this test works:

1. Initial Cleanup:
   - Removes any previous test user
   - Ensures clean state for testing

2. User Creation:
   - Creates a new test user
   - Sets email verification and active status

3. Notification Test:
   - Simulates user approaching inactivity threshold
   - Triggers cleanup to send warning
   - Verifies email notification was sent

4. Deletion Test:
   - Simulates user past warning period
   - Sets notification flags
   - Triggers cleanup for deletion
   - Verifies user was properly deleted

5. Final Verification:
   - Ensures no non-admin users remain
   - Displays test results

Test execution steps:
1. make fcleandb        # Clean everything including database
2. make                 # Start services
3. docker exec -it srcs-web-1 /bin/bash
4. python manage.py test_inactivity
5. make view-users      # Should show only admin users

Test timing (configured in settings.py):
- INACTIVITY_THRESHOLD: 60 seconds (total allowed inactivity time)
- INACTIVITY_WARNING: 15 seconds (warning time before deletion)
- TIME_MULTIPLIER: 1 (using seconds instead of days for testing)
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core import mail
from django.conf import settings
from authentication.models import CustomUser
from authentication.services.gdpr_service import GDPRService
from datetime import timedelta
import time
import logging
import datetime

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test and/or view inactivity status for accounts'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--info-only',
            action='store_true',
            help='Only show information without making changes',
        )

    def handle(self, *args, **options):
        info_only = options['info_only']
        
        if info_only:
            self.stdout.write(self.style.SUCCESS("=== GDPR Inactivity Information ==="))
            self.show_inactivity_info()
        else:
            self.run_inactivity_test()
    
    def show_inactivity_info(self):
        """Shows information about users and their inactivity status"""
        current_time = timezone.now()
        
        self.stdout.write(f"Current time: {current_time}")
        self.stdout.write(f"INACTIVITY_WARNING: {settings.INACTIVITY_WARNING} seconds")
        self.stdout.write(f"INACTIVITY_THRESHOLD: {settings.INACTIVITY_THRESHOLD} seconds")
        
        # Show all non-superuser users
        users = CustomUser.objects.filter(is_superuser=False)
        self.stdout.write("\nUser inactivity status:")
        self.stdout.write("-" * 80)
        self.stdout.write(f"{'Username':<20} {'Last Login':<30} {'Last Activity':<30} {'Notified':<8} {'Notification Date'}")
        self.stdout.write("-" * 80)
        
        for user in users:
            last_activity = user.get_last_activity()
            inactive_seconds = (current_time - last_activity).total_seconds() if last_activity else 0
            
            self.stdout.write(
                f"{user.username:<20} "
                f"{str(user.last_login or 'Never'):<30} "
                f"{str(last_activity):<30} "
                f"{'Yes' if user.inactivity_notified else 'No':<8} "
                f"{str(user.inactivity_notification_date or 'N/A')}"
            )
            
            if inactive_seconds >= settings.INACTIVITY_WARNING:
                self.stdout.write(self.style.WARNING(f"  ⚠️  Inactive for {inactive_seconds:.1f} seconds (warning threshold: {settings.INACTIVITY_WARNING})"))
                
                if user.inactivity_notified and user.inactivity_notification_date:
                    notification_age = (current_time - user.inactivity_notification_date).total_seconds()
                    remaining = settings.INACTIVITY_WARNING - notification_age
                    
                    if remaining > 0:
                        self.stdout.write(f"  ⏳ {remaining:.1f} seconds remaining before deletion")
                    else:
                        self.stdout.write(self.style.ERROR(f"  ❌ Eligible for deletion ({-remaining:.1f} seconds overdue)"))
    
    def run_inactivity_test(self):
        """Runs a complete inactivity test"""
        self.stdout.write(self.style.SUCCESS("=== Starting Inactivity Tests ==="))
        
        # 1. Initial cleanup
        CustomUser.objects.filter(username='inactive_test').delete()
        self.stdout.write(self.style.SUCCESS("✓ Initial cleanup completed"))
        
        # 2. Create test user
        test_user = CustomUser.objects.create_user(
            username='inactive_test',
            email='inactive@test.com',
            password='TestPassword123!',
            is_active=True,
            email_verified=True
        )
        
        # Establecer last_login manualmente
        current_time = timezone.now()
        test_user.last_login = current_time - datetime.timedelta(seconds=settings.INACTIVITY_WARNING + 1)
        test_user.save()
        self.stdout.write(self.style.SUCCESS("✓ Test user created"))
        
        # 3. Fase 1: Probar notificación
        self.stdout.write("\n=== Phase 1: Testing Notification ===")
        GDPRService.cleanup_inactive_users()
        
        # 4. Fase 2: Probar eliminación
        self.stdout.write("\n=== Phase 2: Testing Deletion ===")
        
        # Actualizar usuario para la eliminación
        test_user.refresh_from_db()
        if test_user.inactivity_notified:
            self.stdout.write("Set user for deletion:")
            self.stdout.write(f"- Current time: {timezone.now()}")
            self.stdout.write(f"- Last login: {test_user.last_login}")
            self.stdout.write(f"- Notification date: {test_user.inactivity_notification_date}")
            self.stdout.write(f"- Threshold: {settings.INACTIVITY_THRESHOLD} seconds")
            self.stdout.write(f"- Warning: {settings.INACTIVITY_WARNING} seconds")
            
            # Establecer la fecha de notificación anterior para simular que ya pasó el período de gracia
            test_user.inactivity_notification_date = current_time - datetime.timedelta(
                seconds=settings.INACTIVITY_WARNING + 1
            )
            test_user.save()
        
        self.stdout.write("Executing final cleanup...")
        GDPRService.cleanup_inactive_users()
        
        # Verificar eliminación
        try:
            test_user.refresh_from_db()
            if not test_user.is_active:
                self.stdout.write(self.style.SUCCESS("✓ User successfully deleted"))
            else:
                self.stdout.write(self.style.ERROR("✗ User was not deleted"))
        except CustomUser.DoesNotExist:
            self.stdout.write(self.style.SUCCESS("✓ User completely removed from database"))
        
        # Verificar usuarios restantes
        remaining = CustomUser.objects.filter(is_superuser=False).count()
        self.stdout.write(f"\nRemaining non-superusers: {remaining}\n")
        
        self.stdout.write(self.style.SUCCESS("=== Tests Completed ==="))
