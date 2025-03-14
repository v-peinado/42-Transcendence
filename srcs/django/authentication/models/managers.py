"""
This is for custom User Manager that extends Django's default UserManager
to support soft deletion of users. Instead of physically deleting users from the database,
it marks them as deleted by setting a deletion timestamp (deleted_at). 
Using GDPR guidelines, this allows for better data management and auditing.
"""

from django.contrib.auth.models import UserManager

class CustomUserManager(UserManager):
    def get_queryset(self):
        # By default, only show non-deleted users
        return super().get_queryset().filter(deleted_at__isnull=True)

    def with_deleted(self):
        # Show all users, including deleted ones
        return super().get_queryset()

    def only_deleted(self):
        # Show only deleted users
        return super().get_queryset().filter(deleted_at__isnull=False)

    def create(self, **kwargs):
        # Ensure deleted_at is None when creating
        kwargs['deleted_at'] = None
        return super().create(**kwargs)

    def create_user(self, username, email=None, password=None, **extra_fields):
        # Ensure deleted_at is None when creating user
        extra_fields['deleted_at'] = None
        return super().create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        # Ensure deleted_at is None when creating superuser
        extra_fields['deleted_at'] = None
        return super().create_superuser(username, email, password, **extra_fields)
