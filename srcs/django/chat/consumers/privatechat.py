from .base import ChatConsumer
import json
from django.contrib.auth import get_user_model
from chat.models import PrivateChannel, PrivateChannelMembership
from channels.db import database_sync_to_async

User = get_user_model()

class PrivateConsumer:   
    async def create_private_channel(self, data):
        await self.manage_private_channel(data, 'create')

    async def delete_private_channel(self, data):
        await self.manage_private_channel(data, 'delete')

    async def manage_private_channel(self, data, action):
        user1_id = data.get('user1_id')
        user2_id = data.get('user2_id')
        deleting_user_id = data.get('deleting_user_id')
        other_user_id = user1_id if deleting_user_id == user2_id else user2_id

        if action == 'create':
            channel = await self.create_private_channel_in_db(user1_id, user2_id)
            group_name = channel.name
            await self.add_users_to_group(group_name, [user1_id, user2_id])
        elif action == 'delete':
            await self.delete_private_channel_in_db(data)
            await self.send_user_private_channels()
            await self.notify_user_group(other_user_id)

    async def add_users_to_group(self, group_name, user_ids):
        for user_id in user_ids:
            user_channel_name = ChatConsumer.connected_users.get(user_id)
            if user_channel_name:
                await self.channel_layer.group_add(group_name, user_channel_name)
                await self.channel_layer.group_send(
                    group_name,
                    {
                        'type': 'send_user_private_channels',
                        'user_id': user_id
                    }
                )
        
    async def notify_user_group(self, user_id):
        user_group = f"user_{user_id}"
        await self.channel_layer.group_send(
            user_group,
            {
                'type': 'send_user_private_channels',
                'channel_id': user_id
            }
        )

    async def send_user_private_channels(self, event=None):
        user_id = event.get('user_id', self.user_id) if event else self.user_id
        channels = await self.get_user_private_channels(user_id)
        await self.send(text_data=json.dumps({
            'type': 'private_channels',
            'channels': channels
        }))

    async def join_private_channels(self):
        channels = await self.get_user_private_channels(self.user_id)
        for c in channels:
            channel_name = c["name"]  # e.g., "dm_1_2"
            await self.channel_layer.group_add(channel_name, self.channel_name)

    async def leave_private_channels(self):
        channels = await self.get_user_private_channels(self.user_id)
        for c in channels:
            channel_name = c["name"]  # e.g., "dm_1_2"
            await self.channel_layer.group_discard(channel_name, self.channel_name)

    @database_sync_to_async
    def create_private_channel_in_db(self, user1_id, user2_id):
        user1 = User.objects.get(id=user1_id)
        user2 = User.objects.get(id=user2_id)
        # Construir nombre "dm_minID_maxID"
        channel_name = f"dm_{min(user1_id, user2_id)}_{max(user1_id, user2_id)}"

        # Crear o recuperar el canal en la DB
        channel, created = PrivateChannel.objects.get_or_create(
            user1=self.get_min_user(user1, user2),
            user2=self.get_max_user(user1, user2),
            defaults={'name': channel_name}
        )
        # Crear membresías si el canal es nuevo
        if created:
            PrivateChannelMembership.objects.create(channel=channel, user=user1)
            PrivateChannelMembership.objects.create(channel=channel, user=user2)
        return channel
    
    def get_min_user(self, user1, user2):
        return user1 if user1.id < user2.id else user2

    def get_max_user(self, user1, user2):
        return user1 if user1.id > user2.id else user2
    
    @database_sync_to_async
    def delete_private_channel_in_db(self, data):
        PrivateChannel.objects.filter(
            user1_id = data.get('user1_id'),
            user2_id = data.get('user2_id')
        ).delete()

    @database_sync_to_async
    def get_user_private_channels(self, user_id):
        memberships = PrivateChannelMembership.objects.filter(
            user_id=user_id
        ).select_related('channel')
        channels = []
        for membership in memberships:
            c = membership.channel
            members = PrivateChannelMembership.objects.filter(channel=c).select_related('user')
            channel_members = [{'id': m.user.id, 'username': m.user.username} for m in members]
            channels.append({
                'id': c.id,
                'name': c.name,
                'members': channel_members
            })
        return channels
