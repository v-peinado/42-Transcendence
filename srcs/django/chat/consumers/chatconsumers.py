from .base import ChatConsumer
from .blockusers import BlockConsumer
from .users import UsersConsumer
from .messages import MessagesConsumer
from .friends import FriendRequestsConsumer
from .groups import GroupsConsumer
from .privatechat import PrivateConsumer

from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.contrib.auth import get_user_model
from chat.models import FriendRequest, Friendship, BlockedUser
from channels.db import database_sync_to_async, sync_to_async
from asgiref.sync import sync_to_async
from django.db.models import Q
import logging
from django.core.exceptions import ValidationError

User = get_user_model()
logger = logging.getLogger(__name__)

class MainChatConsumer(
    ChatConsumer,
    FriendRequestsConsumer,
    BlockConsumer,
    MessagesConsumer,
    UsersConsumer,
    GroupsConsumer,
    PrivateConsumer,
):
    # async def receive(self, text_data):
    #     data = json.loads(text_data)
    #     type = data.get("type")

    #     if type == "send_friend_request":
    #         await self.send_friend_request(data)
    #     elif type == "accept_friend_request":
    #         await self.accept_friend_request(data)
    #     elif type == "chat_message":
    #         await self.handle_chat_message(data)
    #     elif type == "private_message":
    #         await self.handle_private_message(data)
    #     elif type == "block_or_unblock_user":
    #         await self.block_or_unblock_user(data)
    #     elif type == 'get_blocked_users':
    #         await self.send_blocked_users(data)
    #     elif type == "remove_friend":
    #         await self.remove_friend(data)
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        channel_name = data.get('channel_name')
        logger.debug(f"Received message: {data}, message type: {message_type}, channel name: {channel_name}")

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