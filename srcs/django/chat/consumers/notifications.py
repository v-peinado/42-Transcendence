import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import datetime

class NotificationsConsumer:
    @staticmethod
    def send_group_notification(tournament_id, message):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"tournament_{tournament_id}",
            {
                'type': 'notification',
                'message': message,
                'created_at': datetime.datetime.now().isoformat()
            }
        )
        
    @staticmethod
    def send_notification(user_id, message):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{user_id}",
            {
                'type': 'notification',
                'message': message,
                'created_at': datetime.datetime.now().isoformat()
            }
        )

    async def handle_notification(self, data):
        message = data.get('message')
        to_user_id = data.get('to_user_id')

        if to_user_id in self.connected_users:
            await self.channel_layer.group_send(
                f"user_{to_user_id}",
                {
                    'type': 'notification',
                    'message': message,
                    'created_at': data.get('created_at')
                }
            )

    async def notification(self, event):
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'message': event['message'],
            'created_at': event['created_at']
        }))
