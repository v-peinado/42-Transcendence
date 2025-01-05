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

class MessagesConsumer:
    #  # Método para manejar mensajes de chat de otros usuarios
    # async def handle_chat_message(self, data):
    #     message = data['message']
    #     await self.channel_layer.group_send(
    #         self.room_group_name,
    #         {
    #             'type': 'chat_message',
    #             'user_id': self.user_id,
    #             'username': self.username,
    #             'message': message,
    #         }
    #     )

    # # Manejar mensajes de chat enviados por uno mismo
    # async def chat_message(self, event):
    #     await self.send(text_data=json.dumps({
    #         'type': 'chat_message',
    #         'user_id': event['user_id'],
    #         'username': event['username'],
    #         'message': event['message'],
    #     }))

    # async def handle_private_message(self, data):
    #     to_user_id = data.get("to_user_id")
    #     message = data.get("message")
    #     from_user = self.scope["user"]

    #     if to_user_id and message:
    #         to_user = await self.get_user_by_id(to_user_id)
            
    #         if await self.is_blocked(from_user.id, to_user.id):
    #             logger.debug(f"User {to_user.username} has blocked {from_user.username}. Private message not sent.")
    #             return

    #         channel_name = await self.get_channel_name(to_user_id)
    #         if channel_name:
    #             await self.channel_layer.send(
    #                 channel_name,
    #                 {
    #                     'type': 'private_message',
    #                     'from_user_id': from_user.id,
    #                     'from_username': from_user.username,
    #                     'message': message
    #                 }
    #             )
    #             logger.debug(f"Private message sent to {to_user.username}.")
    #         else:
    #             await self.send(text_data=json.dumps({
    #                 'type': 'error',
    #                 'message': f'User {to_user.username} is not connected.'
    #             }))
    #             logger.error(f"User {to_user.username} is not connected. Private message not sent.")

    # async def private_message(self, event):
    #     from_user_id = event.get('from_user_id')
    #     from_username = event.get('from_username')
    #     message = event.get('message')
    #     logger.debug(f"Sending private message to {self.scope['user'].username}: {from_username}: {message}")

    #     sender = await sync_to_async(User.objects.get)(id=from_user_id)
    #     if await self.is_blocked(sender.id, self.scope["user"].id):
    #         logger.debug(f"Private message from blocked user {from_username} not sent.")
    #         return

    #     await self.send(text_data=json.dumps({
    #         'type': 'private_message',
    #         'from_user_id': from_user_id,
    #         'from_username': from_username,
    #         'message': message
    #     }))
    
    # Flujo de Mensajes en Django Channels
    # Recepción del Mensaje:

    # Cuando un cliente envía un mensaje a través del WebSocket, el método receive del consumidor lo recibe.
    # El método receive procesa el mensaje y llama a handle_message con los datos del mensaje y el nombre del canal.
    # Manejo del Mensaje:

    # El método handle_message procesa el mensaje y llama a send_to_channel para enviar el mensaje al grupo de canales correspondiente.
    # Si el mensaje es un mensaje directo (DM), handle_message verifica si el destinatario ha bloqueado al remitente antes de enviar el mensaje.
    # Envío al Grupo de Canales:

    # El método send_to_channel utiliza group_send para enviar el mensaje al grupo de canales.
    # group_send envía un evento a todos los consumidores suscritos al grupo de canales especificado. El evento incluye el tipo de mensaje (type) y los datos del mensaje (user_id, username, message, channel_name).
    # Manejo del Evento en el Consumidor:

    # Cada consumidor en el grupo de canales recibe el evento y llama al método correspondiente basado en el tipo de mensaje (type).
    # En este caso, el tipo de mensaje es chat_message, por lo que se llama al método chat_message en cada consumidor.
    # Envío al Cliente:

    # El método chat_message toma los datos del evento y los envía al cliente a través del WebSocket utilizando self.send.
    # self.send envía los datos al cliente en formato JSON.
    
    # Resumen del Flujo
    # Cliente envía mensaje -> receive -> handle_message -> send_to_channel
    # Envío al grupo de canales -> group_send -> chat_message
    # Envío al cliente -> self.send
    
    async def handle_message(self, data, channel_name):
        message = data.get('message')
        from_user = self.scope["user"]
        

        if message:
            if channel_name.startswith('dm_'):
                to_user_ids = channel_name.split('_')[1:]
                user1_id, user2_id = map(int, channel_name.split('_')[1:])
                await self.create_private_channel_in_db(user1_id, user2_id)
                to_user_ids = [int(id) for id in to_user_ids]
                if from_user.id not in to_user_ids:
                    logger.debug(f"User {from_user.username} is not part of the channel {channel_name}. Message not sent.")
                    return

                # Create the private channel if it doesn't exist
                if channel_name not in ChatConsumer.private_channels:
                    ChatConsumer.private_channels[channel_name] = to_user_ids
                    for user_id in to_user_ids:
                        if user_id in ChatConsumer.connected_users:
                            await self.channel_layer.group_add(
                                channel_name,
                                ChatConsumer.connected_users[user_id]
                            )
                    logger.debug(f"Private channel {channel_name} created and users added.")
            logger.debug(f"Sending message from {from_user.username} to channel {channel_name}: {message}")
            await self.send_to_channel(channel_name, from_user.id, from_user.username, message)

    async def send_to_channel(self, channel_name, user_id, username, message):
        await self.channel_layer.group_send(
            channel_name,
            {
                'type': 'chat_message',
                'user_id': user_id,
                'username': username,
                'message': message,
                'channel_name': channel_name,
            }
        )
        logger.debug(f"Message sent to channel {channel_name}: {message}")
        
    async def chat_message(self, event):
        sender_id = event['user_id']
        sender_user = await self.get_user_by_id(sender_id)

        # If this user (self.scope["user"]) is blocking the sender, skip sending
        if await self.is_blocked(self.scope["user"].id, sender_user.id):
            logger.debug(
                f"{self.scope['user'].username} has blocked {sender_user.username}, "
                "so message won't be displayed."
            )
            return

        # Otherwise, proceed with sending the message
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'user_id': sender_id,
            'username': event['username'],
            'message': event['message'],
            'channel_name': event['channel_name'],
        }))
        logger.debug(f"Message sent to client from {event['username']}")