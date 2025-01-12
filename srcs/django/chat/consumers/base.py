from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
import logging

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    connected_users = {}
    private_channels = {}
    
    # Método connect: se ejecuta cuando un usuario se conecta al WebSocket.
    # Se agrega al usuario al grupo de chat y se almacena su nombre de usuario y ID de usuario.
    # También se envía una lista actualizada de usuarios conectados.
    # Este método se ejecuta automáticamente cuando un usuario se conecta al WebSocket.
    async def connect(self):
        # Obtener el nombre de la sala del URL, kwargs es un diccionario que contiene los parámetros de la URL.
        # self hace referenciia a la instancia actual de la clase.
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        # Crear el nombre del grupo de chat, por defecto chat_general
        self.room_group_name = f"chat_{self.room_name}"
        # Obtener el usuario actual, scope es un diccionario que contiene la información de la conexión.
        self.user = self.scope["user"]
        self.username = self.user.username
        self.user_id =  self.user.id # Store user ID

        # Add user to the group
        # channel_layer es un atributo de la instancia de la clase que proporciona acceso a la capa de canales.
        # group_add agrega el canal actual al grupo de chat.
        # channel_name es un atributo de la instancia de la clase que contiene el nombre del canal, que es único para cada conexión.
        # agregamos el canal actual al grupo de chat.
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # f"user_{self.user_id}" es el nombre del grupo específico del usuario. Creamos un grupo para cada usuario.
        # Esto nos permitirá enviar mensajes privados a un usuario específico, como notificaciones de solicitud de amistad, etc.
        await self.channel_layer.group_add(
            f"user_{self.user_id}",
            self.channel_name
        )
        # Map user to their channel
        # Almacenar el nombre del canal del usuario en un diccionario con el ID de usuario como clave.
        ChatConsumer.connected_users[self.user_id] = self.channel_name

        # Aceptar la conexión, esto permite que el usuario se conecte al WebSocket.
        await self.accept()
        
        # Unirse a los canales de grupo y privados almacenaods en la base de datos
        await self.join_group_channels()
        await self.join_private_channels()
        await self.update_all_lists()


    # Método disconnect: se ejecuta cuando un usuario se desconecta del WebSocket.
    # Elimina al usuario del grupo de chat y de la lista de usuarios conectados.
    # También envía una lista actualizada de usuarios conectados.
    # Este método se ejecuta automáticamente cuando un usuario se desconecta del WebSocket.
    async def disconnect(self, close_code):
        ChatConsumer.connected_users.pop(self.user_id, None)
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Salir del grupo específico del usuario
        await self.channel_layer.group_discard(
            f"user_{self.user_id}",
            self.channel_name
        )

        # Saliimos de los canales de grupo y privados almacenados en la base de datos
        await self.leave_group_channels()
        await self.leave_private_channels()
        # Send updated user list
        await self.update_all_lists()
        
    async def update_all_lists(self):
        await self.user_list_update()
        await self.notify_pending_requests(self.scope["user"].id)
        await self.send_friend_list(self.scope["user"].id)
        await self.send_blocked_users()
        await self.send_user_groups()
        await self.send_user_private_channels()
                 
    @database_sync_to_async
    def get_channel_name(self, username):
        return self.connected_users.get(username)