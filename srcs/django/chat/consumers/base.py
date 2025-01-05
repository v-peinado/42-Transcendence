from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.contrib.auth import get_user_model
from chat.models import FriendRequest, Friendship, BlockedUser, PrivateChannel
from channels.db import database_sync_to_async, sync_to_async
from asgiref.sync import sync_to_async
from django.db.models import Q
import logging
from django.core.exceptions import ValidationError

User = get_user_model()
logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    connected_users = {}
    private_channels = {}
    
    # Método connect: se ejecuta cuando un usuario se conecta al WebSocket.
    # Se agrega al usuario al grupo de chat y se almacena su nombre de usuario y ID de usuario.
    # También se envía una lista actualizada de usuarios conectados.
    # Este método se ejecuta automáticamente cuando un usuario se conecta al WebSocket.
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        self.user = self.scope["user"]
        self.username = self.user.username
        self.user_id =  self.user.id # Store user ID

        logger.debug(f"{self.username} attempting to connect to room {self.room_group_name}")

        # Add user to the group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.channel_layer.group_add(
            f"user_{self.user_id}",
            self.channel_name
        )
        # Map user to their channel
        logger.debug(f"{self.username} connected to {self.room_group_name}")
        ChatConsumer.connected_users[self.user_id] = self.channel_name

        await self.accept()
        
        await self.join_group_channels()
        await self.join_private_channels()
        logger.debug(f"{self.username} connected and accepted the connection.")
        await self.update_all_lists()


    # Método disconnect: se ejecuta cuando un usuario se desconecta del WebSocket.
    # Elimina al usuario del grupo de chat y de la lista de usuarios conectados.
    # También envía una lista actualizada de usuarios conectados.
    # Este método se ejecuta automáticamente cuando un usuario se desconecta del WebSocket.
    async def disconnect(self, close_code):
        logger.debug(f"{self.username} is disconnecting from room {self.room_group_name}")
        ChatConsumer.connected_users.pop(self.user_id, None)
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Salir del grupo específico del usuario
        await self.channel_layer.group_discard(
            f"user_{self.user_id}",
            self.channel_name
        )

        await self.leave_group_channels()
        await self.leave_private_channels()
        # Send updated user list
        await self.update_all_lists()
        
    async def update_all_lists(self):
        await self.user_list_update()
        await self.notify_pending_requests(self.scope["user"].id)
        await self.send_friend_list(self.scope["user"].id)
        await self.send_blocked_users()
        await self.send_user_groups()
        await self.send_user_private_channels()
        
    
       
    @database_sync_to_async
    def get_channel_name(self, username):
        return self.connected_users.get(username)