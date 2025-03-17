from .base import ChatConsumer
from .blockusers import BlockConsumer
from .users import UsersConsumer
from .messages import MessagesConsumer
from .friends import FriendRequestsConsumer
from .groups import GroupsConsumer
from .privatechat import PrivateConsumer
from .challenge import ChallengeConsumer
from .notifications import NotificationsConsumer
from .xss_patterns import XSS_PATTERNS
import re
import json
import html
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

    xss_patterns = XSS_PATTERNS

    async def receive(self, text_data):
        """
        Process incoming WebSocket messages with multi-layered XSS protection.

        Implements defense-in-depth by:
        1. Checking raw text for XSS patterns before JSON parsing
        2. Sanitizing the parsed data structure recursively

        This dual protection prevents both parser-level attacks and context-specific
        payloads embedded within valid JSON structures.
        """
        try:
            if await self.contains_xss(text_data):                                              # Check for XSS patterns in the raw text
                logger.warning(
                    f"XSS attempt detected in raw data from user {self.user_id}: {text_data[:100]}..."
                )
                await self.send(
                    text_data=json.dumps(
                        {"type": "error", "message": "Contenido no permitido detectado"}
                    )
                )
                return

            data = json.loads(text_data)
            sanitized_data = await self.sanitize_data(data)                                     # Sanitize the data from the message

            if sanitized_data.get("xss_detected", False):                                       # Check for XSS patterns in the sanitized data
                logger.warning(f"XSS attempt detected in JSON from user {self.user_id}")
                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "error",
                            "message": "Contenido no permitido detectado en el mensaje",
                        }
                    )
                )
                return

            message_type = sanitized_data.get("type")
            channel_name = sanitized_data.get("channel_name")

            if hasattr(self, "handle_message_type"):                                            # Check if the consumer has a message handler
                await self.handle_message_type(
                    message_type, sanitized_data, channel_name
                )

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received from user {self.user_id}")
            await self.send(
                text_data=json.dumps(
                    {"type": "error", "message": "Formato de mensaje inválido"}
                )
            )

    async def contains_xss(self, text):
        """
        Check if the raw text contains any XSS patterns
        """
        if text is None:
            return False

        text_lower = text.lower()

        for pattern in self.xss_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True

        return False

    async def sanitize_data(self, data):
        """
        Recursively sanitize the data structure to prevent XSS attacks, mean to be used after JSON parsing
        Recursive function that sanitizes all strings in a JSON-like data structure, is important the recursive
        nature of this function to sanitize deeply nested data structures.
        """
        if isinstance(data, dict):                                                              # Handle dictionaries of data
            sanitized = {}                                                                      # Create a new dictionary to store the sanitized data
            for key, value in data.items():
                safe_key = key                                                                  # Sanitize the key, but keep the original for nested dictionaries
                if isinstance(value, (dict, list)):                                             # Recursively sanitize nested dictionaries and lists
                    sanitized[safe_key] = await self.sanitize_data(value)
                elif isinstance(value, str):                                                    # Sanitize strings
                    if await self.contains_xss(value):                                          # Check for XSS patterns                                          
                        sanitized["xss_detected"] = True                                        # Mark the data as containing XSS
                        return sanitized
                    sanitized[safe_key] = html.escape(value)                                    # Escape html characters to prevent XSS
                else:
                    sanitized[safe_key] = value
            return sanitized
        elif isinstance(data, list):
            sanitized = []                                                                      # Handle lists of data, similar to dictionaries
            for item in data:
                if isinstance(item, (dict, list)):
                    result = await self.sanitize_data(item)
                    if isinstance(result, dict) and result.get("xss_detected", False):
                        return {"xss_detected": True}
                    sanitized.append(result)
                elif isinstance(item, str):
                    if await self.contains_xss(item):
                        return {"xss_detected": True}
                    sanitized.append(html.escape(item))
                else:
                    sanitized.append(item)
            return sanitized
        return data

    async def handle_message_type(self, message_type, data, channel_name):
        """
        Dispatch the message to the appropriate handler based on the message type.
        """
        logger.debug(f"Handling message type: {message_type}")

        if message_type == "chat_message" and channel_name:
            await self.handle_message(data, channel_name)
        elif message_type == "create_group":
            await self.create_group(data)
        elif message_type == "add_user_to_group":
            await self.add_user_to_group(data)
        elif message_type == "create_private_channel":
            await self.create_private_channel(data)
        elif message_type == "block_user":
            await self.block_or_unblock_user(data)
        elif message_type == "send_friend_request":
            await self.send_friend_request(data)
        elif message_type == "accept_friend_request":
            await self.accept_friend_request(data)
        elif message_type == "reject_friend_request":
            await self.reject_friend_request(data)
        elif message_type == "cancel_friend_request":
            await self.cancel_friend_request(data)
        elif message_type == "delete_friendship":
            await self.delete_friendship(data.get("friendship_id"))
        elif message_type == "delete_private_channel":
            await self.delete_private_channel(data)
        elif message_type == "leave_group":
            await self.leave_group(data)
        elif message_type == "challenge_action" and channel_name:
            await self.handle_challenge_action(data, channel_name)
        elif message_type == "request_channel_messages":
            await self.load_unarchived_messages(self.scope["user"].id)
        elif message_type == "request_online_users":
            await self.user_list_update()
        elif message_type == "get_user_list":
            await self.user_list_update()
        elif message_type == "get_friend_list":
            await self.send_friend_list(self.scope["user"].id)
        elif message_type == "get_pending_requests":
            await self.notify_pending_requests(self.scope["user"].id)
        elif message_type == "get_sent_requests":
            await self.notify_pending_requests(self.scope["user"].id, sent=True)
        else:
            logger.warning(f"Unknown message type: {message_type}")
