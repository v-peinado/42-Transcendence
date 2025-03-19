from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    connected_users = {}
    private_channels = {}

    async def connect(self):
        """
        Connect to the WebSocket, add the user to the chat group, and send the list of connected users.
        """
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]                         # Get the room name from the URL
        self.room_group_name = f"chat_{self.room_name}"                                         # Create a group name, "general" in this case
        self.user = self.scope["user"]                                                          # Get the user from the scope
        self.username = self.user.username
        self.user_id = self.user.id

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)             # Add the user to the general group
        await self.channel_layer.group_add(f"user_{self.user_id}", self.channel_name)           # User-specific group, the user will receive messages only for them
        ChatConsumer.connected_users[self.user_id] = self.channel_name                          # Add the user to the list of connected users
        await self.accept()                                                                     # Accept the WebSocket connection
        await self.join_group_channels()                                                        # Join the group channels
        await self.join_private_channels()                                                      # Join the private channels
        await self.update_all_lists()                                                           # Update the user list, friend list, blocked users list ...
        await self.load_unarchived_messages(self.user_id)                                       # Load unarchived messages

    async def disconnect(self, close_code):
        """
        Disconnect from the WebSocket, remove the user from the chat group, and send the updated list of connected users.
        """
        ChatConsumer.connected_users.pop(self.user_id, None)
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        await self.channel_layer.group_discard(
            f"user_{self.user_id}", self.channel_name
        )
        await self.leave_group_channels()
        await self.leave_private_channels()
        await self.update_all_lists()

    async def update_all_lists(self):
        """
        Update the user list, friend list, blocked users list ...
        """
        await self.user_list_update()
        await self.notify_pending_requests(self.scope["user"].id)
        await self.notify_pending_requests(self.scope["user"].id, sent=True)
        await self.send_friend_list(self.scope["user"].id)
        await self.send_blocked_users()
        await self.send_user_groups()
        await self.send_user_private_channels()
