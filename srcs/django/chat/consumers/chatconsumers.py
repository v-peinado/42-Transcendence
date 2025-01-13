from .base import ChatConsumer
from .blockusers import BlockConsumer
from .users import UsersConsumer
from .messages import MessagesConsumer
from .friends import FriendRequestsConsumer
from .groups import GroupsConsumer
from .privatechat import PrivateConsumer

import json
from django.contrib.auth import get_user_model

User = get_user_model()

class MainChatConsumer(
    ChatConsumer,
    FriendRequestsConsumer,
    BlockConsumer,
    MessagesConsumer,
    UsersConsumer,
    GroupsConsumer,
    PrivateConsumer,
):
   
    async def receive(self, text_data):
        # Recibir un mensaje del cliente, loads convierte el JSON en un diccionario de Python.
        data = json.loads(text_data)
        message_type = data.get('type')
        channel_name = data.get('channel_name')

        # Manejar el mensaje según el tipo, se enviara a la función correspondiente.
        if message_type == 'chat_message' and channel_name:
            await self.handle_message(data, channel_name)
        elif message_type == 'create_group':
            await self.create_group(data)
        elif message_type == 'add_user_to_group':
            await self.add_user_to_group(data)
        elif message_type == 'create_private_channel':
            await self.create_private_channel(data)
        elif message_type == 'block_user':
            await self.block_or_unblock_user(data)
        elif message_type == 'send_friend_request':
            await self.send_friend_request(data)
        elif message_type == 'accept_friend_request':
            await self.accept_friend_request(data)
        elif message_type == 'reject_friend_request':
            await self.reject_friend_request(data)
        elif message_type == 'delete_friendship':
            await self.delete_friendship(data.get('friendship_id'))
        elif message_type == 'delete_private_channel':
            await self.delete_private_channel(data)