from .base import ChatConsumer
from .blockusers import BlockConsumer
from .users import UsersConsumer
from .messages import MessagesConsumer
from .friends import FriendRequestsConsumer

from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.contrib.auth import get_user_model
from chat.models import FriendRequest, Friendship, BlockedUser, Group, GroupMembership, PrivateChannel, PrivateChannelMembership
from channels.db import database_sync_to_async, sync_to_async
from asgiref.sync import sync_to_async
from django.db.models import Q
import logging
from django.core.exceptions import ValidationError

User = get_user_model()
logger = logging.getLogger(__name__)

class PrivateConsumer:
    async def create_private_channel(self, data):
        user1_id = data.get('user1_id')
        user2_id = data.get('user2_id')
        # Crear o recuperar canal de DB
        channel = await self.create_private_channel_in_db(user1_id, user2_id)

        # Usar el channel.name ("dm_minID_maxID") como nombre de grupo
        group_name = channel.name
        await self.channel_layer.group_add(group_name, self.channel_name)

        # Conectar usuarios si están activos
        user1_channel_name = ChatConsumer.connected_users.get(user1_id)
        user2_channel_name = ChatConsumer.connected_users.get(user2_id)
        if user1_channel_name:
            await self.channel_layer.group_add(group_name, user1_channel_name)
        if user2_channel_name:
            await self.channel_layer.group_add(group_name, user2_channel_name)

        # Notificar a ambos de la creación/actualización del canal
        await self.channel_layer.group_send(
            group_name,
            {
                'type': 'notify_private_channel_update',
                'channel_id': channel.id  # Usamos el ID para obtener miembros
            }
        )

    async def notify_private_channel_update(self, event):
        channel_id = event['channel_id']
        members = await self.get_private_channel_members(channel_id)
        for m in members:
            await self.send_user_private_channels(m['id'])

    async def send_user_private_channels(self, user_id=None):
        if user_id is None:
            user_id = self.user_id
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
            logger.debug(f"{self.username} joined private channel {channel_name}")

    async def leave_private_channels(self):
        channels = await self.get_user_private_channels(self.user_id)
        for c in channels:
            channel_name = c["name"]  # e.g., "dm_1_2"
            await self.channel_layer.group_discard(channel_name, self.channel_name)
            logger.debug(f"{self.username} left private channel {channel_name}")

    @database_sync_to_async
    def create_private_channel_in_db(self, user1_id, user2_id):
        user1 = User.objects.get(id=user1_id)
        user2 = User.objects.get(id=user2_id)
        # Construir nombre "dm_minID_maxID"
        channel_name = f"dm_{min(user1_id, user2_id)}_{max(user1_id, user2_id)}"

        # Crear o recuperar el canal en la DB
        channel, created = PrivateChannel.objects.get_or_create(
            user1=min(user1, user2, key=lambda u: u.id),
            user2=max(user1, user2, key=lambda u: u.id),
            defaults={'name': channel_name}
        )
        # Crear membresías si el canal es nuevo
        if created:
            PrivateChannelMembership.objects.create(channel=channel, user=user1)
            PrivateChannelMembership.objects.create(channel=channel, user=user2)
        return channel

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

    @database_sync_to_async
    def get_private_channel_members(self, channel_id):
        memberships = PrivateChannelMembership.objects.filter(
            channel_id=channel_id
        ).select_related('user')
        return [{'id': m.user.id, 'username': m.user.username} for m in memberships]