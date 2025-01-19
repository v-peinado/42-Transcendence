# srcs/django/chat/models.py
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

#settings.AUTH_USER_MODEL: Es una referencia al modelo de usuario personalizado definido en settings.py
#se guarda la clave primaria del usuario
class FriendRequest(models.Model):
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='friend_requests_sent',
        on_delete=models.CASCADE # Si se elimina un usuario, se eliminan todas sus solicitudes de amistad
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='friend_requests_received',
        on_delete=models.CASCADE
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['from_user', 'to_user'], name='unique_friend_request')
        ]

    def __str__(self):
        return f"{self.from_user} -> {self.to_user}"

class Friendship(models.Model):
    user1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='friendship_user1',
        on_delete=models.CASCADE
    )
    user2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='friendship_user2',
        on_delete=models.CASCADE
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user1', 'user2'], name='unique_friendship')
        ]
        
    def clean(self):
        if self.user1 == self.user2:
            raise ValidationError("Un usuario no puede ser amigo de sí mismo.")

    # Sobreescribir el método save para validar los datos antes de guardar
    def save(self, *args, **kwargs):
        self.clean()  # Llama a clean() para realizar validaciones personalizadas
        super().save(*args, **kwargs)  # Llama al método save() de la clase base

    def __str__(self):
        return f"{self.user1} & {self.user2}"
    
class BlockedUser(models.Model):
    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='blocking',
        on_delete=models.CASCADE
    )
    blocked = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='blocked_by',
        on_delete=models.CASCADE
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('blocker', 'blocked')

    def __str__(self):
        return f"{self.blocker} blocked {self.blocked}"

class Group(models.Model):
    name = models.CharField(max_length=255)
    channel_name = models.CharField(max_length=255)  # Nombre único para Channels

    # Sobreescribir el método save para asignar un nombre de canal si no se proporciona
    def save(self, *args, **kwargs):
        if not self.channel_name:
            super().save(*args, **kwargs)  # Guarda primero para obtener el ID
            self.channel_name = f"chat_group_{self.id}"
            super().save(update_fields=['channel_name'])
        else:
            super().save(*args, **kwargs)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='created_groups',
        on_delete=models.SET_NULL,
        null=True  # Permitir valores nulos
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class GroupMembership(models.Model):
    group = models.ForeignKey(
        Group,
        related_name='memberships',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='group_memberships',
        on_delete=models.CASCADE
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['group', 'user'], name='unique_group_membership')
        ]

    def __str__(self):
        return f"{self.user.username} in {self.group.name}"
    
class PrivateChannel(models.Model):
    user1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='private_channels_user1',
        on_delete=models.CASCADE
    )
    user2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='private_channels_user2',
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255, unique=True)  # Agregar el campo name

    class Meta:
        unique_together = ('user1', 'user2')

    def __str__(self):
        return self.name
    
class PrivateChannelMembership(models.Model):
    channel = models.ForeignKey(
        PrivateChannel,
        related_name='memberships',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='private_channel_memberships',
        on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['channel', 'user'], name='unique_private_channel_membership')
        ]

    def __str__(self):
        return f"{self.user.username} in {self.channel}"
    
class ArchivedMessage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    channel_name = models.CharField(max_length=255)
    content = models.TextField()
    timestamp = models.DateTimeField()
    
class Message(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    channel_name = models.CharField(max_length=255)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_archived = models.BooleanField(default=False)