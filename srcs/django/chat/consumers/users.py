import json
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
import logging
from .base import ChatConsumer

User = get_user_model()
logger = logging.getLogger(__name__)


class UsersConsumer:
    async def user_list_update(self):
        users = list(ChatConsumer.connected_users.keys())
        user_list = []
        for user_id in users:
            user_instance = await database_sync_to_async(User.objects.get)(id=user_id)
            user_list.append(
                {
                    "id": user_instance.id,
                    "username": user_instance.username,
                    "is_online": True,
                }
            )

        await self.channel_layer.group_send(
            self.room_group_name, {"type": "send_user_list", "users": user_list}
        )

    async def send_user_list(self, event):
        users = event["users"]
        await self.send(text_data=json.dumps({"type": "user_list", "users": users}))
