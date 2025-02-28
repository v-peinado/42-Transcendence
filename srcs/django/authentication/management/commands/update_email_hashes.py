from django.core.management.base import BaseCommand
from authentication.models import CustomUser

class Command(BaseCommand):
    help = 'Update email hashes for existing users'

    def handle(self, *args, **options):
        users = CustomUser.objects.all()
        for user in users:
            if user.email and not user.email_hash:
                decrypted_email = user.decrypted_email
                if decrypted_email:
                    user.email_hash = user._generate_email_hash(decrypted_email)
                    user.save(update_fields=['email_hash'])
                    self.stdout.write(self.style.SUCCESS(f'Updated hash for user {user.username}'))

