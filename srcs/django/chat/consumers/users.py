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
from .blockusers import BlockConsumer

User = get_user_model()
logger = logging.getLogger(__name__)

class UsersConsumer:
    async def user_list_update(self):
        """
        Recopila la lista de usuarios conectados y la envía a todos los miembros del grupo.
        """
        users = list(ChatConsumer.connected_users.keys())
        user_list = []
        for user_id in users:
            try:
                # Obtener la instancia del usuario
                user_instance = await database_sync_to_async(User.objects.get)(id=user_id)
                user_list.append({
                    'id': user_instance.id,
                    'username': user_instance.username
                })
            except User.DoesNotExist:
                logger.error(f"Usuario {user_id} no encontrado.")
        
        logger.debug(f"Enviando lista actualizada de usuarios a todos: {user_list}")
        
        # Enviar la lista al grupo
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'send_user_list',
                'users': user_list
            }
        )
    
    async def send_user_list(self, event):
        """
        Manejador para enviar la lista de usuarios al WebSocket.
        """
        users = event['users']
        await self.send(text_data=json.dumps({
            'type': 'user_list',
            'users': users
        }))
    
    @database_sync_to_async
    def get_user_by_username(self, username):
        return User.objects.get(username=username)
