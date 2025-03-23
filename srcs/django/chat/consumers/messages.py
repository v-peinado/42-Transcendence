import json
from django.contrib.auth import get_user_model
from .base import ChatConsumer
from .blockusers import BlockedUser  
from channels.db import database_sync_to_async
from chat.models import (
    Message,
    PrivateChannelMembership,
    GroupMembership,
    PrivateChannel,
)
import logging
# Import XSS detection and sanitization
from .xss_sanitization import detect_xss, render_code_safely, is_already_processed

User = get_user_model()

logger = logging.getLogger(__name__)

class MessagesConsumer:
    """
    Message Flow Pipeline:

    1. Reception:
    - Client sends message via WebSocket -> receive method processes it -> calls handle_message

    2. Processing:
    - handle_message processes data and calls send_to_channel
    - checks if recipient has blocked sender before sending

    3. Channel Distribution:
    - send_to_channel uses group_send to broadcast to all consumers in the channel group
    - Event includes message type and data (user_id, username, message, channel_name)

    4. Consumer Handling:
    - Each consumer in the channel group receives the event
    - Calls the method corresponding to the event type (chat_message)

    5. Client Delivery:
    - chat_message method formats data and sends to client via WebSocket (self.send)

    Flow Summary: Client -> receive -> handle_message -> send_to_channel -> group_send -> chat_message -> self.send
    """
    async def handle_message(self, data, channel_name):
        """
        Handle a message sent by the user.
        Stores the original message in the database and sanitizes it only when sending to clients.
        The prefix 'dm_' is used to identify private messages, followed by the user ids of the users in the conversation.
        """
        message = data.get("message")
        from_user = self.scope["user"]

        if message:
            is_dangerous = data.get("_has_xss_in_message", False)                               # Check if chatconsumers.py already detected XSS
            if not is_dangerous:
                is_dangerous = detect_xss(message)
            await self.save_message(from_user, channel_name, message)                           # Store the ORIGINAL message in the database (not sanitized)   
            if is_dangerous:                                                                    # If the message contains dangerous code, sanitize it BEFORE sending
                sanitized_message = render_code_safely(message)
            else:
                sanitized_message = message

            if channel_name.startswith("dm_"):
                to_user_ids = channel_name.split("_")[1:]
                user1_id, user2_id = map(int, channel_name.split("_")[1:])                      # Map the user ids to integers, user1_id and user2_id
                to_user_ids = [user1_id, user2_id]

                ChatConsumer.private_channels[channel_name] = to_user_ids                       # Add the private channel to the private_channels dictionary

                for user_id in to_user_ids:                                                     # Add the users to the group
                    if user_id in ChatConsumer.connected_users:                                 
                        await self.channel_layer.group_add(
                            channel_name, ChatConsumer.connected_users[user_id]
                        )
            
            await self.send_to_channel(
                channel_name, from_user.id, from_user.username, sanitized_message
            )

    async def send_to_channel(self, channel_name, user_id, username, message):
        """
        Send a message to the channel. The message is sent to all consumers in the channel group.
        If the recipient has blocked the sender, the message will not be sent.
        """
        await self.channel_layer.group_send(
            channel_name,
            {
                "type": "chat_message",
                "user_id": user_id,
                "username": username,
                "message": message,
                "channel_name": channel_name,
            },
        )

    async def chat_message(self, event):
        """
        Method called when a message is received from the channel layer.
        Send the message to the client.
        If the sender is blocked, the message will not be sent.
        """
        sender_id = event["user_id"]
        sender_user = await self.get_user_by_id(sender_id)

        if await self.is_blocked(self.scope["user"].id, sender_user.id):                        # If the sender is blocked, return
            return

        message = event["message"]                                                              # The message is already sanitized from send_to_channel

        await self.send(
            text_data=json.dumps(
                {
                    "type": "chat_message",
                    "user_id": sender_id,
                    "username": event["username"],
                    "message": message,
                    "channel_name": event["channel_name"],
                }
            )
        )

    async def load_unarchived_messages(self, user_id):
        """
        Load unarchived messages for the user. Archive messages are not sent to the user(Not implemented).
        The messages are sent to the user in the order they were sent and to the correct channel.
        Sanitizes messages when loading them from the database, not before storing them.
        """
        logger.info(f"Loading unarchived messages for user {user_id}")
        channels = await self.get_user_channels(user_id)
        for channel_name in channels:
            messages = await self.get_unarchived_messages_filtered(                             # Get the unarchived messages for the user, filtered by blocked users
                user_id, channel_name
            )
            logger.info(
                f"Loading {len(messages)} unarchived messages for channel {channel_name}"
            )
            for message in messages:
                content = message.content                                                       # Get the original content from the database
            
                if detect_xss(content):                                                         # Detect if it contains dangerous code
                    sanitized_content = render_code_safely(content)                             # Sanitize only if necessary
                else:
                    sanitized_content = content                                                 # Don't modify safe content

                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "chat_message",
                            "user_id": await self.get_user_id(message),
                            "username": await self.get_username(message),
                            "message": sanitized_content,
                            "channel_name": message.channel_name,
                            "timestamp": message.timestamp.isoformat(),
                        }
                    )
                )

    def is_already_escaped(self, text):
        """
        Verify if the text is already escaped.
        """
        return is_already_processed(text)

    @database_sync_to_async
    def get_unarchived_messages_filtered(self, user_id, channel_name):
        """
        This method filters out messages from blocked users.
        """
        blocked_users = BlockedUser.objects.filter(blocker_id=user_id).values_list(
            "blocked_id", flat=True
        )

        return list(
            Message.objects.filter(channel_name=channel_name, is_archived=False)
            .exclude(user_id__in=blocked_users)
            .order_by("timestamp")
        )

    @database_sync_to_async
    def get_user_id(self, message):
        return message.user.id if message.user else None

    @database_sync_to_async
    def get_username(self, message):
        return message.user.username if message.user else None

    @database_sync_to_async
    def get_user_channels(self, user_id):
        """
        Get the channels for the user, user the membership tables to get the channels.
        """
        private_channels = PrivateChannelMembership.objects.filter(
            user_id=user_id
        ).values_list("channel__name", flat=True)

        group_channels = GroupMembership.objects.filter(user_id=user_id).values_list(
            "group__channel_name", flat=True
        )

        return list(private_channels) + list(group_channels) + ["chat_general"]

    @database_sync_to_async
    def save_message(self, user, channel_name, content):
        Message.objects.create(
            user=user,
            channel_name=channel_name,
            content=content,
        )