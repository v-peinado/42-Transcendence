from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.contrib.auth import get_user_model
from chat.models import FriendRequest, Friendship, BlockedUser
from channels.db import database_sync_to_async, sync_to_async
from asgiref.sync import sync_to_async
from django.db.models import Q
import logging
from django.core.exceptions import ValidationError
from .base import ChatConsumer

User = get_user_model()
logger = logging.getLogger(__name__)

class FriendRequestsConsumer:
    async def send_friend_request(self, data):
        to_user_id = data.get('to_user_id')
        if not to_user_id:
            await self.send_error('to_user_id missing')
            return

        from_user = await self.get_user_by_id(self.user_id)
        to_user = await self.get_user_by_id(to_user_id)
        friend_request, created = await self.create_friend_request(from_user, to_user)
        if not created:
            await self.send_error('Friend request already exists')
            return

        # Notificar al emisor que la solicitud se ha enviado correctamente
        await self.send(text_data=json.dumps({
            'type': 'friend_request_sent',
            'to_user_id': to_user.id,
            'to_username': to_user.username,
            'from_user_id': from_user.id,
            'from_username': from_user.username,
            'request_id': friend_request.id
        }))

        # Notificar al receptor sobre la nueva solicitud pendiente
        await self.notify_pending_requests(to_user_id)

    async def accept_friend_request(self, data):
        request_id = data.get('request_id')
        if not request_id:
            await self.send_error('Friend request ID not provided.')
            return

        try:
            friend_request = await self.get_friend_request(request_id)
            if friend_request.to_user_id != self.user_id:
                await self.send_error('No tienes permiso para aceptar esta solicitud.')
                return

            # Crear la amistad
            await self.create_friendship(friend_request.from_user_id, friend_request.to_user_id)
            # Eliminar la solicitud pendiente
            await self.delete_friend_request(friend_request)

            from_user = await self.get_user_by_id(friend_request.from_user_id)
            to_user = await self.get_user_by_id(friend_request.to_user_id)

            # Notificar a ambos usuarios sobre la aceptación
            await self.notify_pending_requests(from_user.id)
            await self.notify_pending_requests(to_user.id)

            # También puedes notificar sobre la actualización de la lista de amistades
            await self.send_friend_list(from_user.id)
            await self.send_friend_list(to_user.id)

        except FriendRequest.DoesNotExist:
            await self.send_error('Friend request not found.')
        except Exception as e:
            await self.send_error(f'Error al aceptar la solicitud: {str(e)}')
            
    async def reject_friend_request(self, data):
        request_id = data.get('request_id')
        if not request_id:
            await self.send_error('Friend request ID not provided.')
            return

        try:
            friend_request = await self.get_friend_request(request_id)
            if friend_request.to_user_id != self.user_id:
                await self.send_error('No tienes permiso para rechazar esta solicitud.')
                return

            # Eliminar la solicitud pendiente
            await self.delete_friend_request(friend_request)

            from_user = await self.get_user_by_id(friend_request.from_user_id)
            to_user = await self.get_user_by_id(friend_request.to_user_id)

            # Notificar al emisor y receptor sobre la eliminación de la solicitud
            await self.notify_pending_requests(from_user.id)
            await self.notify_pending_requests(to_user.id)

        except FriendRequest.DoesNotExist:
            await self.send_error('Friend request not found.')
        except Exception as e:
            await self.send_error(f'Error al rechazar la solicitud: {str(e)}')

    async def notify_pending_requests(self, user_id):
        """Enviar la lista actualizada de solicitudes pendientes al usuario especificado."""
        pending_data = await self.get_pending_requests_data(user_id)
        pending_list = [
            {
                'request_id': req['id'],
                'from_user_id': req['from_user_id'],
                'from_user_username': req['from_user__username']
            }
            for req in pending_data
        ]

        # Enviar al grupo correspondiente
        await self.channel_layer.group_send(
            f"user_{user_id}",
            {
                'type': 'pending_list',
                'pending': pending_list
            }
        )
            
    async def pending_list(self, event):
        """Maneja el envío de solicitudes pendientes al usuario destino."""
        await self.send(text_data=json.dumps({
            'type': 'pending_friend_requests',
            'pending': event['pending']
        }))
        
    async def send_friend_list(self, user_id):
        """Enviar la lista actualizada de amistades al usuario especificado."""
        friends = await self.get_friends(user_id)
        await self.channel_layer.group_send(
            f"user_{user_id}",
            {
                'type': 'friend_list_update',
                'friends': friends
            }
        )

    async def friend_list_update(self, event):
        """Manejar el envío de la lista de amistades al usuario."""
        await self.send(text_data=json.dumps({
            'type': 'friend_list_update',
            'friends': event['friends']
        }))

    async def send_error(self, message):
        await self.send(text_data=json.dumps({'type': 'error', 'message': message}))

    @database_sync_to_async
    def get_user_by_id(self, user_id):
        return User.objects.get(id=user_id)

    @database_sync_to_async
    def get_friend_request(self, request_id):
        return FriendRequest.objects.get(id=request_id)

    @database_sync_to_async
    def create_friend_request(self, from_user, to_user):
        return FriendRequest.objects.get_or_create(from_user=from_user, to_user=to_user)

    @database_sync_to_async
    def create_friendship(self, from_user_id, to_user_id):
        if from_user_id > to_user_id:
            from_user_id, to_user_id = to_user_id, from_user_id
        Friendship.objects.create(user1_id=from_user_id, user2_id=to_user_id)

    @database_sync_to_async
    def delete_friend_request(self, friend_request):
        friend_request.delete()
        
    @database_sync_to_async
    def get_friendship(self, friendship_id):
        return Friendship.objects.get(id=friendship_id)
    
    async def delete_friendship(self, friendship_id):
        friendship = await self.get_friendship(friendship_id)
        user1 = friendship.user1_id
        user2 = friendship.user2_id
        await self.delete_friendship_append(friendship_id)
        # Notificar a ambos usuarios sobre la eliminación de la amistad
        await self.send_friend_list(user1)
        await self.send_friend_list(user2)
        
    @database_sync_to_async    
    def delete_friendship_append(self, friendship_id):
        friendship = Friendship.objects.get(id=friendship_id)
        friendship.delete()
        
        
    @database_sync_to_async
    def get_friends(self, user_id):
        return list(
            Friendship.objects.filter(Q(user1_id=user_id) | Q(user2_id=user_id))
            .select_related('user1', 'user2')
            .values('user1_id', 'user1__username', 'user2_id', 'user2__username', 'id')
        )

    @database_sync_to_async
    def get_pending_requests_data(self, user_id):
        # Convert to list so it’s safe to iterate
        return list(
            FriendRequest.objects.filter(to_user_id=user_id)
            .select_related('from_user')
            .values('id', 'from_user_id', 'from_user__username')
        )