"""
How this test works:

1. Initial Setup:
   - Clean state by removing any existing test user
   - Ensures reproducible test environment

2. User Creation & Setup:
   - Creates new test user with specific conditions
   - Sets email verification status
   - Sets inactivity conditions:
     * Last login past threshold
     * Notification flag enabled
     * Notification date past warning period

3. Cleanup Execution:
   - Runs GDPR cleanup service
   - Simulates what Celery task would do in production

4. Result Verification:
   - Checks if user was properly deleted
   - Verifies cleanup was successful

5. Final State Check:
   - Confirms no non-admin users remain
   - Ensures complete cleanup

Test execution steps:
1. make fcleandb        # Clean everything including database
2. make                 # Start services
3. docker exec -it srcs-web-1 /bin/bash
4. python manage.py test_task
5. make view-users      # Should show zero users

Test timing (configured in settings.py):
- INACTIVITY_THRESHOLD = 60  # 60 seconds in test, 60 days in production
- INACTIVITY_WARNING = 15    # 15 seconds in test, 15 days in production
- TIME_MULTIPLIER = 1        # 1 for testing (seconds), 86400 for production (days)
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from authentication.models import CustomUser
from authentication.services.gdpr_service import GDPRService
from datetime import timedelta
from django.conf import settings

class Command(BaseCommand):
    help = 'Test task execution for GDPR cleanup'

    def handle(self, *args, **kwargs):
        # 1. Cleanup any existing test user
        CustomUser.objects.filter(username='test_task').delete()
        self.stdout.write('✓ Cleaned up previous test user')

        # 2. Create test user
        user = CustomUser.objects.create_user(
            username='test_task',
            email='test@task.com',
            password='test123'
        )
        user.email_verified = True
        user.is_active = True
        user.last_login = timezone.now() - timedelta(seconds=settings.INACTIVITY_THRESHOLD * 2)
        user.inactivity_notified = True
        user.inactivity_notification_date = timezone.now() - timedelta(seconds=settings.INACTIVITY_WARNING * 2)
        user.save()
        self.stdout.write('✓ Created test user with inactivity conditions')

        # 3. Run cleanup
        self.stdout.write('Running cleanup...')
        GDPRService.cleanup_inactive_users()

        # 4. Verify results
        exists = CustomUser.objects.filter(username='test_task').exists()
        if exists:
            self.stdout.write(self.style.ERROR('❌ Test failed: User was not deleted'))
        else:
            self.stdout.write(self.style.SUCCESS('✓ Test passed: User was deleted'))

        # 5. Show remaining users
        total_users = CustomUser.objects.exclude(is_superuser=True).count()
        self.stdout.write(f'\nRemaining non-superusers: {total_users}')
