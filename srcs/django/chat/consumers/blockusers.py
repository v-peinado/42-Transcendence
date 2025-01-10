import json
from django.contrib.auth import get_user_model
from chat.models import BlockedUser
from channels.db import database_sync_to_async, sync_to_async
from asgiref.sync import sync_to_async

User = get_user_model()

class BlockConsumer:
    # Bloquear o desbloquear a un usuario, se recibe el ID del usuario a bloquear/desbloquear
    # Se comprueba si el usuario ya está bloqueado, si lo está se desbloquea, si no se bloquea.   
    async def block_or_unblock_user(self, data):
        user_id = data.get('user_id')
        user = await self.get_user_by_id(user_id)
        from_user = self.scope["user"]
        is_currently_blocked = await self.is_blocked(from_user.id, user.id)

        if is_currently_blocked:
            await self.unblock_user(from_user, user)
            type = 'unblocked'
        else:
            await self.block_user(from_user, user)
            type = 'blocked'
            
        # Enviar un mensaje al usuario actual sobre el bloqueo/desbloqueo
        await self.send(text_data=json.dumps({
            'type': type,
            'username': user.username
        }))
       
        await self.send_blocked_users()

    async def is_blocked(self, blocker_id, blocked_id):
        return await database_sync_to_async(BlockedUser.objects.filter(
            blocker_id=blocker_id,
            blocked_id=blocked_id
        ).exists)()

    # Bloquear a un usuario
    async def block_user(self, blocker, blocked):
        await sync_to_async(BlockedUser.objects.create)(
            blocker=blocker,
            blocked=blocked
        )
    
    # Desbloquear a un usuario
    async def unblock_user(self, blocker, blocked):
        await sync_to_async(BlockedUser.objects.filter(
            blocker=blocker,
            blocked=blocked
        ).delete)()

    # Obtener la lista de usuarios bloqueados
    async def get_blocked_users(self, user):
        # Usamos list() para convertir el queryset en una lista de diccionarios, es necesario porque no se puede serializar un queryset.
        # Una lista es basicamente un campo serializable, ejemplo: [{'username': 'user1'}, {'username': 'user2'}]
        #select_related('blocked') se utiliza para obtener los datos del campo blocked en la misma consulta.
        blocked = await sync_to_async(list)(BlockedUser.objects.filter(
            blocker=user
        ).select_related('blocked'))
        # retornamos de cada acciion de bloqueo b, del bloqueado blocked, el username
        return [{'username': b.blocked.username} for b in blocked]
    
    # Enviar la lista de usuarios bloqueados al cliente
    async def send_blocked_users(self):
        blocked_users = await self.get_blocked_users(self.scope["user"])
        # json.dumps() convierte un objeto de Python en una cadena JSON.
        await self.send(text_data=json.dumps({
            'type': 'blocked_users',
            'blocked_users': blocked_users
        }))
    
    @database_sync_to_async
    def get_user_by_id(self, user_id):
        return User.objects.get(id=user_id)