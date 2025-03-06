from .base import ChatConsumer
from .blockusers import BlockConsumer
from .users import UsersConsumer
from .messages import MessagesConsumer
from .friends import FriendRequestsConsumer
from .groups import GroupsConsumer
from .privatechat import PrivateConsumer
from .challenge import ChallengeConsumer
from .notifications import NotificationsConsumer

import json
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class MainChatConsumer(
    ChatConsumer,
    FriendRequestsConsumer,
    BlockConsumer,
    MessagesConsumer,
    UsersConsumer,
    GroupsConsumer,
    PrivateConsumer,
    ChallengeConsumer,
    NotificationsConsumer,
):
   
    async def receive(self, text_data):
        # Recibir un mensaje del cliente, loads convierte el JSON en un diccionario de Python.
        data = json.loads(text_data)
        message_type = data.get('type')
        channel_name = data.get('channel_name')

        # Manejar el mensaje según el tipo, se enviara a la función correspondiente.
        await self.handle_message_type(message_type, data, channel_name)

    async def handle_message_type(self, message_type, data, channel_name):
        """
        Método implementado para manejar los diferentes tipos de mensajes
        después de que han sido sanitizados
        """
        logger.debug(f"Handling message type: {message_type}")
        
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
        elif message_type == 'cancel_friend_request':
            await self.cancel_friend_request(data)
        elif message_type == 'delete_friendship':
            await self.delete_friendship(data.get('friendship_id'))
        elif message_type == 'delete_private_channel':
            await self.delete_private_channel(data)
        elif message_type == 'leave_group':
            await self.leave_group(data)
        elif message_type == 'challenge_action' and channel_name:
            await self.handle_challenge_action(data, channel_name)
        elif message_type == 'request_channel_messages':
            await self.load_unarchived_messages(self.scope['user'].id)
        # Manejar los tipos de mensajes faltantes
        elif message_type == 'request_online_users':
            await self.user_list_update()
        elif message_type == 'get_user_list':
            await self.user_list_update()
        elif message_type == 'get_friend_list':
            await self.send_friend_list(self.scope['user'].id)
        elif message_type == 'get_pending_requests':
            await self.notify_pending_requests(self.scope['user'].id)
        elif message_type == 'get_sent_requests':
            await self.notify_pending_requests(self.scope['user'].id, sent=True)
        else:
            logger.warning(f"Unknown message type: {message_type}")