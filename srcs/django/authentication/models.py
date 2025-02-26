from django.contrib.sessions.models import Session
from django.utils import timezone
from django.db import models

class UserSession(models.Model):
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE)
    session = models.ForeignKey('sessions.Session', on_delete=models.CASCADE)  # Corregido para usar el modelo correcto de sesión
    last_activity = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'session')
