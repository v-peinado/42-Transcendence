from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from ..models import Game
from ..engine.game_state import GameState
import json
import asyncio

# Clase de consumidor de WebSocket para el juego

class GameConsumer(AsyncJsonWebsocketConsumer):
    game_states = {}																# Diccionario de estados de juego compartidos

    async def connect(self):														# Conexión inicial (al abrir el socket)
        self.game_id = self.scope['url_route']['kwargs']['game_id']					# Obtener el ID del juego desde la URL
        self.room_group_name = f'game_{self.game_id}'								# Nombre de grupo para el juego (enviar mensajes a todos los jugadores)
        self.user = self.scope['user']												# Usuario actual conectado
        self.game_state = None  # Inicializamos a None
        
        await self.channel_layer.group_add(											# Agregar al usuario al grupo del juego
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()															# Aceptar la conexión
        
		# Inicializar el estado del juego
        game = await self.get_game()												# Obtener el juego actual
        if game:																	# Si el juego existe (no es None)
            if self.game_id not in self.game_states:								# Si no hay un estado de juego para este juego
                self.game_states[self.game_id] = GameState()						# Crear un nuevo estado de juego (por ejemplo, un nuevo juego)
            self.game_state = self.game_states[self.game_id]						# Obtener el estado de juego actual
            
            # Configurar modo single player
            if game.game_mode == 'SINGLE':
                self.game_state.is_single_player = True
                self.game_state.difficulty = game.difficulty
                self.player_side = 'left'  # El jugador humano siempre en la izquierda
                
                # Iniciar juego inmediatamente en modo single player
                await self.start_single_player_game(game)
            else:
                # Lógica existente para modo multiplayer
                player1 = await self.get_player1(game)
                player2 = await self.get_player2(game)
                
                print(f"Current user: {self.user.id}, Player1: {player1.id if player1 else None}")
                
                # Asignación del lado en el que jugará el usuario
                if player1 and player1.id == self.user.id:								# Si el jugador 1 es el usuario actual...
                    self.player_side = 'left'
                    print(f"Assigned as left paddle to user {self.user.id}")
                elif not player2:														# Si ya hay un jugador 1 y no hay un jugador 2...
                    self.player_side = 'right'
                    print(f"Assigned as right paddle to user {self.user.id}")
                else:																	# Si el usuario no es jugador 1 ni jugador 2...
                    self.player_side = None
                    print(f"User {self.user.id} is a spectator")						# --> El usuario es un espectador

                if game.status == 'WAITING' and player1 != self.user and not player2:	# Si el juego está en espera y el jugador 1 no eres tú y no hay un jugador 2...
                    await self.update_game(game)										# Actualizar el juego con el jugador 2
                    await self.channel_layer.group_send(								# Enviar mensaje de inicio de juego
                        self.room_group_name,
                        {
                            'type': 'game_start',	
                            'player1': player1.username,
                            'player2': self.user.username,
                            'player1_id': player1.id,
                            'player2_id': self.user.id
                        }
                    )

                if game.status == 'PLAYING':											# Si el juego está en curso...
                    self.game_state.status = 'playing'
                    print(f"Game is PLAYING, starting loop for {self.player_side}")
                    asyncio.create_task(self.game_loop())								# Iniciar el loop del juego

	# Métodos auxiliares para obtener información de la db (de forma asíncrona para no bloquear el hilo principal)
    
    @database_sync_to_async
    def get_game(self):																# Obtener el id del juego actual
        try:
            return Game.objects.get(id=self.game_id)
        except Game.DoesNotExist:
            return None

    @database_sync_to_async
    def get_player1(self, game):													# Obtener el jugador 1 del juego
        return game.player1

    @database_sync_to_async
    def get_player2(self, game):													# Obtener el jugador 2 del juego
        return game.player2

    @database_sync_to_async
    def update_game(self, game):													# Actualizar el juego con el jugador 2
        game.player2 = self.user
        game.status = 'PLAYING'
        game.save()

    @database_sync_to_async
    def update_game_status(self, game, status):
        game.status = status
        game.save()

	# Métodos de WebSocket para manejar la conexión y los mensajes
    
    async def disconnect(self, close_code):											# Desconexión (al cerrar el socket)
        if hasattr(self, 'game_id') and self.game_id in self.game_states:			# Si hay un id de juego y un estado de juego para ese id...
            del self.game_states[self.game_id]										# Eliminar el id del juego del diccionario de estados de juego
        await self.channel_layer.group_discard(										# Eliminar al usuario del grupo del juego
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):												# Recibir mensaje de WebSocket (texto)
        data = json.loads(text_data)
        print(f"Received raw data: {data}")  # Debug log
        await self.receive_json(data)

    async def receive_json(self, content):											# Recibir mensaje de WebSocket (JSON)
        message_type = content.get('type')
        
        if message_type == 'change_difficulty' and self.game_state.is_single_player:
            self.game_state.difficulty = content.get('difficulty', 'medium')
            # Actualizar velocidad de la pelota según dificultad
            settings = self.game_state.DIFFICULTY_SETTINGS[self.game_state.difficulty]
            self.game_state.ball.speed_x = settings['BALL_SPEED'] * (1 if self.game_state.ball.speed_x > 0 else -1)
            self.game_state.ball.speed_y = settings['BALL_SPEED']
            
        elif message_type == 'move_paddle':											# Si el mensaje es para mover una paleta...
            side = content.get('side')
            try:
                direction = int(content.get('direction', 0))
                if not -1 <= direction <= 1:  										# Si la dirección no es válida (puede ser -1, 0 o 1)...
                    print(f"Invalid direction value: {direction}")
                    return
                    
                if side == self.player_side and self.game_state:					# Si el lado es el mismo que el del jugador actual y hay un estado de juego...
                    current_y = self.game_state.paddles[side].y						# Guardar la posición actual de la paleta
                    
                    self.game_state.move_paddle(side, direction)					# Mover la paleta
                    new_y = self.game_state.paddles[side].y							# Obtener la nueva posición de la paleta
                    
                    state = self.game_state.serialize()								# Serializar el estado del juego (para enviarlo al resto de jugadores)
                    
                    if current_y != new_y:  										# Solo enviar actualización si la posición cambió
                        await self.channel_layer.group_send(
                            self.room_group_name,
                            {
                                'type': 'game_state_update',
                                'state': state
                            }
                        )
            except ValueError:														# Si la dirección no es un número...
                print(f"Invalid direction format: {content.get('direction')}")
        # elif message_type == 'start_game':
        #     self.game_state.game_status = 'playing'
            
        # elif message_type == 'pause_game':
        #     self.game_state.game_status = 'paused'

    async def game_start(self, event):												# Iniciar el juego
        if self.game_state:															# Si hay un estado de juego...
            self.game_state.start_countdown()										# Iniciar la cuenta regresiva
            asyncio.create_task(self.countdown_timer())								# Iniciar el temporizador de cuenta regresiva
        await self.send(text_data=json.dumps(event))								# Enviar mensaje de inicio de juego

    async def countdown_timer(self):												# Temporizador de cuenta regresiva
        for count in range(3, 0, -1):												# Contar desde 3 hasta 1
            self.game_state.countdown = count
            
            await self.channel_layer.group_send(									# Enviar mensaje a todos los jugadores 
                self.room_group_name,
                {
                    'type': 'game_state_update',
                    'state': self.game_state.serialize()
                }
            )
            
            await asyncio.sleep(1.2)  												# Aumentamos ligeramente el tiempo para compensar latencias
        
        self.game_state.countdown_active = False									# Al finalizar la cuenta regresiva..
        self.game_state.status = 'playing'											# Cambiar el estado del juego a 'playing'
        
        await self.channel_layer.group_send(										# Enviamos una última actualización con el estado final
            self.room_group_name,
            {
                'type': 'game_state_update',	
                'state': self.game_state.serialize()
            }
        )
        
        asyncio.create_task(self.game_loop())										# Iniciar el loop del juego

    async def game_loop(self):														# Loop del juego
        while True:
            if hasattr(self, 'game_state') and self.game_state.status == 'playing':	# Si hay un estado de juego y el juego está en curso...
                timestamp = asyncio.get_event_loop().time()  # Obtener timestamp actual
                self.game_state.update(timestamp)  # Pasar el timestamp al método update
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'game_state_update',
                        'state': self.game_state.serialize()
                    }
                )
            await asyncio.sleep(1/60)  												# 60 FPS

    async def game_state_update(self, event):										# Actualizar el estado del juego (enviado por otro jugador)
        await self.send(text_data=json.dumps({
            'type': 'game_state',
            'state': event['state']
        }))

    async def start_single_player_game(self, game):
        """Inicia una partida en modo single player"""
        if game.status == 'WAITING':
            await self.update_game_status(game, 'PLAYING')
            
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_start',
                'player1': self.user.username,
                'player2': 'CPU',
                'player1_id': self.user.id,
                'player2_id': None
            }
        )
        
        # Iniciar el juego
        self.game_state.status = 'playing'
        asyncio.create_task(self.game_loop())