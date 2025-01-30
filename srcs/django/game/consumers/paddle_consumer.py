# from channels.generic.websocket import AsyncJsonWebsocketConsumer
# from channels.db import database_sync_to_async
# from ..models import Game

# class PaddleConsumer(AsyncJsonWebsocketConsumer):
#     async def connect(self):
#         self.game_id = self.scope['url_route']['kwargs']['game_id']
#         self.side = self.scope['url_route']['kwargs']['side']
#         self.room_group_name = f'game_{self.game_id}_paddle_{self.side}'
        
#         await self.channel_layer.group_add(
#             self.room_group_name,
#             self.channel_name
#         )
#         await self.accept()
#         print(f"PaddleConsumer: Conectado para {self.side} en juego {self.game_id}")

#     async def receive_json(self, content):
#         print(f"PaddleConsumer: Recibido movimiento para {self.side}: {content}")
#         if content.get('type') == 'move_paddle':
#             await self.channel_layer.group_send(
#                 f'game_{self.game_id}',
#                 {
#                     'type': 'paddle_movement',
#                     'side': self.side,
#                     'direction': content.get('direction')
#                 }
#             )