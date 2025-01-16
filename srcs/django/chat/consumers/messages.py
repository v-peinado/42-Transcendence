import json
from django.contrib.auth import get_user_model
from .base import ChatConsumer

User = get_user_model()

class MessagesConsumer:   
    # Flujo de Mensajes
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
            if channel_name.startswith('dm_'): # Si el canal es un mensaje directo
                to_user_ids = channel_name.split('_')[1:] # [:1], asi extraemos el primer elemento de la lista, ej: [4 , 2]
                # Usaremos map para aplicar el int() a cada elemento de la lista y guardarlo en user1_id = 4 y user2_id = 2
                user1_id, user2_id = map(int, channel_name.split('_')[1:])
                
                to_user_ids = [user1_id, user2_id]

                # Si no existe el canal privado en el diccionario de canales privados, lo añadimos
                # si no esta bloqueado, el nombre de canal se guardara en la db y se hara un add al grupo
                # en la clase PrivateChatConsumer
                # Si esta bloqueado no se guardara en la db y no se hara un add al grupo cuando se conecte, por lo
                # hasta que no se vuelva a enviar un mensaje no se volvera a intentar añadir al grupo
                ChatConsumer.private_channels[channel_name] = to_user_ids
                    # Añadimos a ambos usuarios al canal privado
                for user_id in to_user_ids:
                    if user_id in ChatConsumer.connected_users:
                            await self.channel_layer.group_add(
                                channel_name,
                                ChatConsumer.connected_users[user_id]
                            )
            # Enviamos el mensaje al canal, el cual puede ser un canal privado o un grupo
            # Al enviarlo al canal, se enviará a todos los consumidores suscritos al canal
            await self.send_to_channel(channel_name, from_user.id, from_user.username, message)

    async def send_to_channel(self, channel_name, user_id, username, message):
        # Enviamos el mensaje al grupo del canal
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
    
    # El evento chat_message es manejado por cada consumidor en el grupo del canal
    async def chat_message(self, event):
        sender_id = event['user_id']
        sender_user = await self.get_user_by_id(sender_id)

        # Si el mensaje proviene de un usuario bloqueado, no se mostrará
        if await self.is_blocked(self.scope["user"].id, sender_user.id):
            return

        # Se envía el mensaje al cliente
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'user_id': sender_id,
            'username': event['username'],
            'message': event['message'],
            'channel_name': event['channel_name'],
        }))