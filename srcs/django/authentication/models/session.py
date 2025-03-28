from django.contrib.sessions.models import Session
from django.utils import timezone
from django.db import models

#This model is used to store the user session information

class UserSession(models.Model):
    user = models.ForeignKey('authentication.CustomUser', on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    last_activity = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'session')
        app_label = 'authentication'

    def __str__(self):
        return f"{self.user.username} - {self.last_activity}"
