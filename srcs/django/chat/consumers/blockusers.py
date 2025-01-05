from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.contrib.auth import get_user_model
from chat.models import FriendRequest, Friendship, BlockedUser
from channels.db import database_sync_to_async, sync_to_async
from asgiref.sync import sync_to_async
from django.db.models import Q
import logging
from django.core.exceptions import ValidationError
from .base import ChatConsumer

User = get_user_model()
logger = logging.getLogger(__name__)

class BlockConsumer:    
    async def block_or_unblock_user(self, data):
        user_id = data.get('user_id')
        user = await self.get_user_by_id(user_id)
        from_user = self.scope["user"]
        is_currently_blocked = await self.is_blocked(from_user.id, user.id)

        if is_currently_blocked:
            await self.unblock_user(from_user, user)
            message = f'Desbloqueado usuario con ID {user_id}.'
            status = 'unblocked'
        else:
            await self.block_user(from_user, user)
            message = f'Bloqueado usuario con ID {user_id}.'
            status = 'blocked'

        await self.send(text_data=json.dumps({
            'type': 'block_or_unblock_user',
            'status': status,
            'message': message,
            'user_id': user_id
        }))
        await self.send_blocked_users()

    async def is_blocked(self, blocker_id, blocked_id):
        return await database_sync_to_async(BlockedUser.objects.filter(
            blocker_id=blocker_id,
            blocked_id=blocked_id
        ).exists)()

    # Bloquear a un usuario
    async def block_user(self, blocker, blocked):
        await sync_to_async(BlockedUser.objects.create)(
            blocker=blocker,
            blocked=blocked
        )
    
    # Desbloquear a un usuario
    async def unblock_user(self, blocker, blocked):
        await sync_to_async(BlockedUser.objects.filter(
            blocker=blocker,
            blocked=blocked
        ).delete)()

    # Obtener la lista de usuarios bloqueados
    async def get_blocked_users(self, user):
        blocked = await sync_to_async(list)(BlockedUser.objects.filter(
            blocker=user
        ).select_related('blocked'))
        return [{'username': b.blocked.username} for b in blocked]
    
    # Enviar la lista de usuarios bloqueados al cliente
    async def send_blocked_users(self):
        blocked_users = await self.get_blocked_users(self.scope["user"])
        await self.send(text_data=json.dumps({
            'type': 'blocked_users',
            'blocked_users': blocked_users
        }))
        logger.debug("Lista de usuarios bloqueados enviada al cliente.")
    
    @database_sync_to_async
    def get_user_by_id(self, user_id):
        return User.objects.get(id=user_id)