
import json
from django.contrib.auth import get_user_model
from chat.models import FriendRequest, Friendship
from channels.db import database_sync_to_async
from django.db.models import Q

User = get_user_model()

class FriendRequestsConsumer:
    async def send_friend_request(self, data):
        to_user_id = data.get('to_user_id')

        from_user = await self.get_user_by_id(self.user_id)
        to_user = await self.get_user_by_id(to_user_id)
        
        # Verificar si ya existe una relación de amistad
        already_friends = await self.check_friendship_exists(from_user, to_user)
        if already_friends:
            return await self.send_error('You are already friends.')
        # Al poner , created, se obtiene una tupla con dos valores, el objeto y un booleano que indica si se ha creado o no,
        # gracias a la heramienta get_or_create de Django, que se usa en la funciion create_friend_request.
        # si no se ha podido crear porque ya existe, se envía un error.
        friend_request, created = await self.create_friend_request(from_user, to_user)
        if not created:
            return await self.send_error('Friend request already exists')
       
        # Actualizar al receptor sobre la nueva solicitud pendiente
        await self.notify_pending_requests(to_user_id)

    async def accept_friend_request(self, data):
        request_id = data.get('request_id')
        if not request_id:
            await self.send_error('Friend request ID not provided.')
            return

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

        # Actualización de la lista de amistades
        await self.send_friend_list(from_user.id)
        await self.send_friend_list(to_user.id)
            
    async def reject_friend_request(self, data):
        request_id = data.get('request_id')
        if not request_id:
            await self.send_error('Friend request ID not provided.')
            return

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
        
    # FLUJO DE EVENTOS:       
    # Envió de Datos:
    # notify_pending_requests obtiene y formatea las solicitudes pendientes, 
    # luego envía un mensaje al grupo de canales del usuario con el tipo 'pending_list'.

    # Manejo del Evento:
    # La función pending_list detecta el evento 'pending_list', extrae los datos de solicitudes pendientes y 
    # los envía al cliente WebSocket asociado.

    # Actualización del Cliente:
    # El cliente WebSocket recibe el mensaje JSON con las solicitudes pendientes y
    # puede actualizar la interfaz de usuario en consecuencia.

    async def notify_pending_requests(self, user_id):
        # Obtener las solicitudes pendientes del usuario identificado por user_id
        pending_data = await self.get_pending_requests_data(user_id)
        # Crearemos una lista de diccrionarios de solicitudes pendientes
        pending_list = []
        for req in pending_data:
            pending_list.append({
                'request_id': req['id'],
                'from_user_id': req['from_user_id'],
                'from_user_username': req['from_user__username']
            })

        # Enviar la lista de solicitudes pendientes al grupo de canales del usuario
        await self.channel_layer.group_send(
            f"user_{user_id}",  # Nombre del grupo basado en user_id
            {
                'type': 'pending_list',  # Tipo de evento que será manejado por el método pending_list
                'pending': pending_list    # Carga útil con la lista de solicitudes pendientes
            }
        )
            
    async def pending_list(self, event):
        # Enviar los datos de solicitudes pendientes al cliente WebSocket en formato JSON
        await self.send(text_data=json.dumps({
            'type': 'pending_friend_requests',  # Tipo de mensaje que indica solicitudes pendientes
            'pending': event['pending']        # Lista de solicitudes pendientes recibida del evento
        }))
        
    async def send_friend_list(self, user_id):
        friends = await self.get_friends(user_id)
        await self.channel_layer.group_send(
            f"user_{user_id}",  # Format string, se usa para incrustar expresiones dentro de una cadena
            {
                'type': 'friend_list_update',
                'friends': friends
            }
        )

    async def friend_list_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'friend_list_update',
            'friends': event['friends']
        }))

    async def send_error(self, message):
        await self.send(text_data=json.dumps({'type': 'error', 'message': message}))

    @database_sync_to_async
    def get_friend_request(self, request_id):
        return FriendRequest.objects.get(id=request_id)
    
    # La clase Q en Django se utiliza para construir consultas complejas 
    # que involucran operadores lógicos como AND, OR y NOT. 
    # Permite combinar condiciones de filtrado de manera flexible en las consultas ORM.
    @database_sync_to_async
    def check_friendship_exists(self, from_user, to_user):
        return Friendship.objects.filter(
            Q(user1=from_user, user2=to_user) | Q(user1=to_user, user2=from_user)
        ).exists()
        
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
        # Convertimos en lista el query de amistades, para poder serializarlo
        return list(
            Friendship.objects.filter(Q(user1_id=user_id) | Q(user2_id=user_id))
            .select_related('user1', 'user2')
            .values('user1_id', 'user1__username', 'user2_id', 'user2__username', 'id')
        )

    @database_sync_to_async
    def get_pending_requests_data(self, user_id):
        return list(
            FriendRequest.objects.filter(to_user_id=user_id)
            .select_related('from_user')
            .values('id', 'from_user_id', 'from_user__username')
        )