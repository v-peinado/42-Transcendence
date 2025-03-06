from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
import asyncio
import re
import json
import html
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    connected_users = {}
    private_channels = {}
    
    # Lista de patrones XSS mejorada para filtrar
    XSS_PATTERNS = [
        r'<script[\s\S]*?>[\s\S]*?</script>',  # Script tags
        r'<\s*img[^>]*\sonerror\s*=',  # Image onerror
        r'<\s*img[^>]*\ssrc\s*=\s*["\']?\s*javascript:',  # JavaScript in src
        r'javascript\s*:',  # JavaScript protocol
        r'<\s*svg[^>]*\sonload\s*=',  # SVG onload
        r'<\s*iframe',  # iframes
        r'<\s*object',  # object tags
        r'<\s*embed',  # embed tags
        r'<\s*form',  # form tags (potential CSRF)
        r'<\s*base',  # base tags
        r'<\s*link',  # link tags
        r'<\s*meta',  # meta tags
        r'on\w+\s*=\s*["\']?',  # Event handlers (onclick, onload, etc.)
        r'data\s*:(?!image/)',  # Data URIs except safe images
        r'src\s*=\s*["\']?\s*data:',  # Src with data URIs
        r'expression\(.*\)',  # CSS expressions
        r'document\.(?:cookie|write|createelement)',  # DOM manipulation
        r'(?:window|self|this|top|parent|frames)\.',  # Window object references
        r'eval\(.*\)',  # Eval
        r'setInterval\(.*\)',  # Timer functions
        r'setTimeout\(.*\)',
        r'Function\(.*\)',  # Function constructor
        r'alert\(.*\)',  # Alert dialog
        r'confirm\(.*\)',  # Confirm dialog
        r'prompt\(.*\)',  # Prompt dialog
    ]
    
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
               
        # Llamar a la función para enviar los mensajes no archivados
        await self.load_unarchived_messages(self.user_id)


    # Método disconnect: se ejecuta cuando un usuario se desconecta del WebSocket.
    # Elimina al usuario del grupo de chat y de la lista de usuarios conectados.
    # También envía una lista actualizada de usuarios conectados.
    # Este método se ejecuta automáticamente cuando un usuario se desconecta del WebSocket.
    # close_code es un código que indica la razón por la que se cerró la conexión, si la conexión se cerró correctamente, el código será 1000.
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
        await self.notify_pending_requests(self.scope["user"].id, sent=True)
        await self.send_friend_list(self.scope["user"].id)
        await self.send_blocked_users()
        await self.send_user_groups()
        await self.send_user_private_channels()
        
    async def receive(self, text_data):
        """
        Recibir mensaje del WebSocket, filtrar contenido malicioso y procesar
        """
        try:
            # Primero validamos si el texto en sí contiene patrones XSS
            if await self.contains_xss(text_data):
                logger.warning(f"XSS attempt detected in raw data from user {self.user_id}: {text_data[:100]}...")
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Contenido no permitido detectado'
                }))
                return
                
            # Parsear el JSON
            data = json.loads(text_data)
            
            # Validar cada campo del mensaje que podría contener texto
            sanitized_data = await self.sanitize_data(data)
            
            # Si se encontró contenido malicioso durante la sanitización
            if sanitized_data.get('xss_detected', False):
                logger.warning(f"XSS attempt detected in JSON from user {self.user_id}")
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Contenido no permitido detectado en el mensaje'
                }))
                return
            
            # Continuar con el procesamiento usando los datos sanitizados
            message_type = sanitized_data.get('type')
            channel_name = sanitized_data.get('channel_name')
            
            # Este es un método que debe implementar cada consumidor heredado
            # para manejar los diferentes tipos de mensajes
            if hasattr(self, 'handle_message_type'):
                await self.handle_message_type(message_type, sanitized_data, channel_name)
            
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received from user {self.user_id}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Formato de mensaje inválido'
            }))
    
    async def contains_xss(self, text):
        """Detectar patrones XSS en el texto"""
        if text is None:
            return False
            
        text_lower = text.lower()
        
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
                
        return False
    
    async def sanitize_data(self, data):
        """Sanitiza los datos del mensaje recursivamente"""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                # Sanitizar las claves
                safe_key = key
                
                # Sanitizar los valores
                if isinstance(value, (dict, list)):
                    sanitized[safe_key] = await self.sanitize_data(value)
                elif isinstance(value, str):
                    # Verificar XSS en strings
                    if await self.contains_xss(value):
                        sanitized['xss_detected'] = True
                        return sanitized
                    # Sanitizar HTML para strings seguros
                    sanitized[safe_key] = html.escape(value)
                else:
                    sanitized[safe_key] = value
            return sanitized
        elif isinstance(data, list):
            sanitized = []
            for item in data:
                if isinstance(item, (dict, list)):
                    result = await self.sanitize_data(item)
                    if isinstance(result, dict) and result.get('xss_detected', False):
                        return {'xss_detected': True}
                    sanitized.append(result)
                elif isinstance(item, str):
                    if await self.contains_xss(item):
                        return {'xss_detected': True}
                    sanitized.append(html.escape(item))
                else:
                    sanitized.append(item)
            return sanitized
        return data
    
    async def handle_message_type(self, message_type, data, channel_name):
        """
        Método que debe ser implementado por consumidores heredados
        para manejar los diferentes tipos de mensajes
        """
        # Este método debe ser sobreescrito por subclases
        pass