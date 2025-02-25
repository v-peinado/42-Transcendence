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

class Command(BaseCommand):
    help = 'Test user inactivity cleanup with different scenarios'

    def handle(self, *args, **kwargs):
        # Test initialization
        self.stdout.write(self.style.SUCCESS('\n=== Starting Inactivity Tests ===\n'))

        # 1. Initial cleanup
        CustomUser.objects.filter(username='inactive_test').delete()
        self.stdout.write('✓ Initial cleanup completed')

        # 2. Create test user
        user = CustomUser.objects.create_user(
            username='inactive_test',
            email='inactive@test.com',
            password='test123'
        )
        user.email_verified = True
        user.is_active = True
        user.save()
        self.stdout.write('✓ Test user created')

        # 3. Test notification phase
        self.stdout.write('\n=== Phase 1: Testing Notification ===')
        # Set last login to trigger warning but not deletion
        user.last_login = timezone.now() - timedelta(
            seconds=settings.INACTIVITY_THRESHOLD - (settings.INACTIVITY_WARNING / 2)
        )
        user.save()
        
        mail.outbox = []
        GDPRService.cleanup_inactive_users()
        
        # Verify notification email
        if len(mail.outbox) > 0:
            self.stdout.write(self.style.SUCCESS(
                '✓ Warning email sent:\n'
                f'  Subject: {mail.outbox[0].subject}\n'
                f'  To: {mail.outbox[0].to}\n'
            ))

        # 4. Test deletion phase
        self.stdout.write('\n=== Phase 2: Testing Deletion ===')
        user.refresh_from_db()
        
        # Force conditions for immediate deletion
        user.last_login = timezone.now() - timedelta(seconds=settings.INACTIVITY_THRESHOLD * 2)
        user.inactivity_notified = True
        user.inactivity_notification_date = timezone.now() - timedelta(
            seconds=settings.INACTIVITY_WARNING * 2
        )
        user.save()
        
        # Wait for changes to take effect
        time.sleep(1)
        
        # Execute final cleanup
        self.stdout.write('Executing final cleanup...')
        GDPRService.cleanup_inactive_users()
        
        # Verify deletion
        exists = CustomUser.objects.filter(username='inactive_test').exists()
        if exists:
            # If deletion failed, show detailed user state
            self.stdout.write(self.style.ERROR('❌ Error: User was not deleted'))
            user = CustomUser.objects.get(username='inactive_test')
            self.stdout.write(f"""
Current user state:
- Last login: {user.last_login}
- Notified: {user.inactivity_notified}
- Notification date: {user.inactivity_notification_date}
- Active: {user.is_active}
- Inactive time: {(timezone.now() - user.last_login).total_seconds()} seconds
- Inactivity threshold: {settings.INACTIVITY_THRESHOLD} seconds
- Warning time: {settings.INACTIVITY_WARNING} seconds
""")
        else:
            self.stdout.write(self.style.SUCCESS('✓ User successfully deleted'))

        # 5. Final verification
        total_users = CustomUser.objects.exclude(is_superuser=True).count()
        self.stdout.write(f'\nRemaining non-superusers: {total_users}')
        
        self.stdout.write(self.style.SUCCESS('\n=== Tests Completed ===\n'))
        
		# Steps to use this command:
		# 1. docker exec -it srcs-web-1 /bin/bash
		# 2. python manage.py test_inactivity
        # 3. exit
        # 4. make view-users