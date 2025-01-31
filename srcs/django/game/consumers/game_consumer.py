from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from ..models import Game
from ..engine.game_state import GameState
import json
import asyncio

class GameConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.room_group_name = f'game_{self.game_id}'
        self.user = self.scope['user']
        self.player_side = None
        self.game_state = GameState()
        self.shared_game_state = None  # Añadir estado compartido
        self.game_state.status = 'playing'
        self.paddle_speed = 20  # Aumentar velocidad
        self.last_paddle_positions = {'left': 150, 'right': 150}

        print(f"[CONNECT] Player {self.user.username} connecting to game {self.game_id}")
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Iniciar el game loop
        self.game_loop_task = asyncio.create_task(self.game_loop())
        
        try:
            game = await self.get_game()
            if game:
                game_player1 = await self.get_player1(game)
                game_player2 = await self.get_player2(game)
                
                # Determinar el lado del jugador
                if str(game_player1.id) == str(self.user.id):
                    self.player_side = 'left'
                    print(f"[CONNECT] {self.user.username} assigned as LEFT player")
                else:
                    self.player_side = 'right'
                    print(f"[CONNECT] {self.user.username} assigned as RIGHT player")
                    if not game_player2:
                        await self.update_game(game)

                # Enviar estado inicial
                await self.send_json({
                    'type': 'game_start',
                    'player1_id': str(game_player1.id),
                    'player2_id': str(game_player2.id) if game_player2 else None,
                })

                # Enviar estado del juego inicial
                await self.send_json({
                    'type': 'game_state',
                    'state': self.game_state.serialize()
                })
        except Exception as e:
            print(f"[ERROR] Error in connect: {str(e)}")

    @database_sync_to_async
    def get_game(self):
        try:
            return Game.objects.select_related('player1', 'player2').get(id=self.game_id)
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
        # Cancelar el game loop al desconectar
        if hasattr(self, 'game_loop_task'):
            self.game_loop_task.cancel()
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        # Implementar lógica de recepción de datos

    async def receive_json(self, content):
        """Handle incoming WebSocket messages"""
        message_type = content.get('type')
        print(f"[RECEIVE] Message type: {message_type}, Content: {content}")
        
        if message_type == 'move_paddle':
            side = content.get('side')
            direction = int(content.get('direction'))  # Forzar int
            timestamp = content.get('timestamp')
            
            print(f"[MOVE] Received move command: side={side}, direction={direction}, time={timestamp}")
            
            if side == self.player_side:
                # Mover la paleta directamente
                paddle = self.game_state.paddles[side]
                new_y = paddle.y + (direction * self.paddle_speed)
                
                # Aplicar límites
                max_y = self.game_state.canvas_height - paddle.height
                paddle.y = max(0, min(new_y, max_y))
                
                print(f"[PADDLE] Moved {side} paddle to y={paddle.y}")
                
                # Broadcast inmediato del nuevo estado
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'game_state_update',
                        'state': self.game_state.serialize(),
                        'movement': {'side': side, 'y': paddle.y}
                    }
                )

    async def game_start(self, event):
        """Send game start event with player IDs"""
        event['player1_id'] = str(self.user.id) if self.player_side == 'left' else None
        await self.send(text_data=json.dumps(event))

    async def game_loop(self):
        """Loop principal del juego"""
        print("[GAME] Starting game loop")
        while True:
            try:
                if hasattr(self, 'game_state') and self.game_state.status == 'playing':
                    self.game_state.update()
                    # Solo enviar actualizaciones de la pelota
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'game_state_update',
                            'state': self.game_state.serialize(),
                            'ball_only': True
                        }
                    )
                await asyncio.sleep(1/60)  # Aumentado a 60 FPS
            except Exception as e:
                print(f"[ERROR] Game loop error: {str(e)}")

    async def game_state_update(self, event):
        """Enviar actualización del estado del juego al cliente"""
        if 'paddle_move' in event:
            print(f"[UPDATE] Paddle move update: {event['paddle_move']}")
        await self.send_json({
            'type': 'game_state',
            'state': event['state']
        })