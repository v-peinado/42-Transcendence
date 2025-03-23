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
# Update imports to include new functions
from .xss_sanitization import detect_xss, render_code_safely, is_already_processed
import re
import json
import logging
from django.contrib.auth import get_user_model

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
        3. Neutralizing potential malicious content while preserving message flow
        """
        try:
            xss_detected_raw = detect_xss(text_data)                                            # Check for XSS patterns in the raw text
            
            if xss_detected_raw:
                logger.warning(
                    f"XSS attempt detected in raw data from user {self.user_id}"
                )
                await self.send(                                                                # Notify the user of the detected XSS                                                              
                    text_data=json.dumps(
                        {"type": "warning", "message": "Potentially malicious content detected"}
                    )
                )
            
            data = json.loads(text_data)
            
            full_xss_check_result = await self.check_xss_in_data(data)                          # Check for XSS in all fields, including message
            
            
            if data.get("type") == "chat_message":
                sanitized_data = await self.sanitize_non_message_fields(data)                   # For chat messages, sanitize everything except the message content
                if full_xss_check_result.get("has_xss_in_message", False):                      # If the message field has XSS, mark it for messages.py to know
                    sanitized_data["_has_xss_in_message"] = True
            else:
                sanitized_data = await self.sanitize_data(data)                                 # For other types of data, sanitize everything as before
            
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
                    {"type": "error", "message": "Invalid message format"}
                )
            )

    async def contains_xss(self, text):
        """
        Check if the raw text contains any XSS patterns.
        Uses the improved detection function.
        """
        return detect_xss(text)

    async def check_xss_in_data(self, data):
        """
        Check for XSS in all fields including message, but don't sanitize.
        Returns information about XSS presence in different parts of the data.
        """
        result = {"has_xss": False, "has_xss_in_message": False}
        
        if isinstance(data, dict):                                                              # Handle dictionaries of data
            for key, value in data.items():
                if isinstance(value, (dict, list)):                                             # Recursively check nested dictionaries and lists                   
                    sub_result = await self.check_xss_in_data(value)                            # Check for XSS in the nested data
                    if sub_result.get("has_xss", False):                                        # If XSS is found, mark the parent data as having XSS           
                        result["has_xss"] = True                                                
                elif isinstance(value, str):
                    if await self.contains_xss(value):
                        result["has_xss"] = True
                        if key == "message" and data.get("type") == "chat_message":
                            result["has_xss_in_message"] = True
        
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    sub_result = await self.check_xss_in_data(item)
                    if sub_result.get("has_xss", False):
                        result["has_xss"] = True
                elif isinstance(item, str):
                    if await self.contains_xss(item):
                        result["has_xss"] = True
        
        return result

    async def sanitize_non_message_fields(self, data):
        """
        Sanitize only non-message fields in chat messages.
        This prevents sanitizing the actual message content that will be stored.
        """
        if not isinstance(data, dict):
            return data
            
        sanitized = {}
        for key, value in data.items():
            if key == "message" and data.get("type") == "chat_message":
                sanitized[key] = value
            elif isinstance(value, (dict, list)):
                sanitized[key] = await self.sanitize_data(value)                                
            elif isinstance(value, str):
                if await self.contains_xss(value):
                    sanitized[key] = render_code_safely(value)
                else:
                    sanitized[key] = value
            else:
                sanitized[key] = value
                
        return sanitized

    async def sanitize_data(self, data):
        """
        Recursively sanitizes data to prevent XSS attacks.
        Uses the render_code_safely function to display code as text.
        """
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    sanitized[key] = await self.sanitize_data(value)
                elif isinstance(value, str):
                    if await self.contains_xss(value):
                        sanitized[key] = render_code_safely(value)
                    else:
                        sanitized[key] = value
                else:
                    sanitized[key] = value
            return sanitized
            
        elif isinstance(data, list):
            sanitized = []
            for item in data:
                if isinstance(item, (dict, list)):
                    sanitized.append(await self.sanitize_data(item))
                elif isinstance(item, str):
                    if await self.contains_xss(item):
                        # Use our improved render_code_safely function
                        sanitized.append(render_code_safely(item))
                    else:
                        sanitized.append(item)
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