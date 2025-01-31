from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from ..models import Game
from ..engine.game_state import GameState
import json
import asyncio

class GameConsumer(AsyncJsonWebsocketConsumer):
    # Variable de clase para compartir el estado del juego
    game_states = {}

    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.room_group_name = f'game_{self.game_id}'
        self.user = self.scope['user']
        self.game_state = None  # Inicializamos a None
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        game = await self.get_game()
        if game:
            # Usar un estado compartido para el mismo juego
            if self.game_id not in self.game_states:
                self.game_states[self.game_id] = GameState()
            self.game_state = self.game_states[self.game_id]
            
            # Asignar rol al jugador actual
            player1 = await self.get_player1(game)
            player2 = await self.get_player2(game)
            
            print(f"Current user: {self.user.id}, Player1: {player1.id if player1 else None}")
            
            # Asignación de lado más clara
            if player1 and player1.id == self.user.id:
                self.player_side = 'left'
                print(f"Assigned as left paddle to user {self.user.id}")
            elif not player2:
                self.player_side = 'right'
                print(f"Assigned as right paddle to user {self.user.id}")
            else:
                self.player_side = None
                print(f"User {self.user.id} is a spectator")

            if game.status == 'WAITING' and player1 != self.user and not player2:
                await self.update_game(game)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'game_start',
                        'player1': player1.username,
                        'player2': self.user.username,
                        'player1_id': player1.id,
                        'player2_id': self.user.id
                    }
                )

            if game.status == 'PLAYING':
                self.game_state.status = 'playing'
                print(f"Game is PLAYING, starting loop for {self.player_side}")
                asyncio.create_task(self.game_loop())

    @database_sync_to_async
    def get_game(self):
        try:
            return Game.objects.get(id=self.game_id)
        except Game.DoesNotExist:
            return None

    @database_sync_to_async
    def get_player1(self, game):
        return game.player1

    @database_sync_to_async
    def get_player2(self, game):
        return game.player2

    @database_sync_to_async
    def update_game(self, game):
        game.player2 = self.user
        game.status = 'PLAYING'
        game.save()

    async def disconnect(self, close_code):
        if hasattr(self, 'game_id') and self.game_id in self.game_states:
            del self.game_states[self.game_id]
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        print(f"Received raw data: {data}")  # Debug log
        await self.receive_json(data)

    async def receive_json(self, content):
        """Handle incoming WebSocket messages"""
        message_type = content.get('type')
        print(f"Received message type: {message_type} with content: {content}")
        
        if message_type == 'move_paddle':
            side = content.get('side')
            try:
                direction = int(content.get('direction', 0))
                if not -1 <= direction <= 1:  # Validar que direction sea -1, 0 o 1
                    print(f"Invalid direction value: {direction}")
                    return
                    
                if side == self.player_side and self.game_state:
                    print(f"Valid move request for {side} paddle with direction {direction}")
                    current_y = self.game_state.paddles[side].y
                    print(f"Before move: paddle {side} at y={current_y}")
                    
                    self.game_state.move_paddle(side, direction)
                    new_y = self.game_state.paddles[side].y
                    print(f"After move: paddle {side} at y={new_y}")
                    
                    state = self.game_state.serialize()
                    print(f"Serialized paddle position: {state['paddles'][side]['y']}")
                    
                    if current_y != new_y:  # Solo enviar actualización si la posición cambió
                        await self.channel_layer.group_send(
                            self.room_group_name,
                            {
                                'type': 'game_state_update',
                                'state': state
                            }
                        )
            except ValueError:
                print(f"Invalid direction format: {content.get('direction')}")
        elif message_type == 'start_game':
            self.game_state.game_status = 'playing'
            
        elif message_type == 'pause_game':
            self.game_state.game_status = 'paused'

    async def game_start(self, event):
        """Maneja el evento de inicio del juego"""
        await self.send(text_data=json.dumps(event))

    async def game_loop(self):
        """Loop principal del juego"""
        while True:
            if hasattr(self, 'game_state') and self.game_state.status == 'playing':
                self.game_state.update()  # Esto ahora actualizará también las paletas
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'game_state_update',
                        'state': self.game_state.serialize()
                    }
                )
            await asyncio.sleep(1/60)  # 60 FPS

    async def game_state_update(self, event):
        """Enviar actualización del estado del juego"""
        await self.send(text_data=json.dumps({
            'type': 'game_state',
            'state': event['state']
        }))