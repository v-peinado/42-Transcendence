from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    email_verification_token = models.CharField(max_length=255, null=True, blank=True)
    email_token_created_at = models.DateTimeField(null=True, blank=True)
