import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import datetime


class NotificationsConsumer:
    @staticmethod
    def send_notification(user_id, message):
        """
        This function sends a notification to a specific user.(Local tournament notifications)
        """
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{user_id}",
            {
                "type": "notification",
                "message": message,
                "created_at": datetime.datetime.now().isoformat(),
            },
        )

    async def notification(self, event):
        """
        Send the notification to the user client.
        """
        await self.send(
            text_data=json.dumps(
                {
                    "type": "notification",
                    "message": event["message"],
                    "created_at": event["created_at"],
                }
            )
        )
