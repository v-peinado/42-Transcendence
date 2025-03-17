import json
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from game.models import Game
import logging
from django.db import transaction

User = get_user_model()

logger = logging.getLogger(__name__)

class ChallengeConsumer():
    async def handle_challenge_action(self, data, channel_name):
        action = data.get('action')  # 'challenge', 'reject', 'accept'
        from_user = await self.get_user_by_id(data.get('from_user_id'))
        to_user_username = data.get('to_username')
        to_user = await self.get_user_by_username(to_user_username)

        if action == 'challenge':
            message = data.get('message', '')
        elif action == 'reject':
            message = f"{to_user.username} ha rechazado tu invitación :("
        elif action == 'accept':
            game = await self.create_game(from_user, to_user)
            message = f"{to_user.username} ha aceptado tu invitación :)"
        else:
            return

        await self.channel_layer.group_send(
            channel_name,
            {
                'type': 'challenge_action_message',
                'action': action,
                'from_user_id': from_user.id,
                'from_username': from_user.username,
                'to_user_id': to_user.id,
                'to_username': to_user.username,
                'channel_name': channel_name,
                'message': message,
                'game_id': game.id if action == 'accept' else None
            }
        )

    async def challenge_action_message(self, event):
        msg = {
            'type': 'challenge_action',
            'action': event['action'],
            'from_user_id': event['from_user_id'],
            'from_username': event['from_username'],
            'to_user_id': event['to_user_id'],
            'to_username': event['to_username'],
            'channel_name': event['channel_name'],
            'message': event['message'],
            'game_id': event['game_id'],
        }
        await self.send(text_data=json.dumps(msg))

    @database_sync_to_async
    def get_user_by_username(self, username):
        return User.objects.filter(username=username).first()
    
    @database_sync_to_async
    def create_game(self, player1, player2):
        """Create a new game with the given players"""
        with transaction.atomic():
            game = Game.objects.create(
                player1=player1,
                player2=player2,
                status='WAITING',
                player1_ready=True,
                player2_ready=True 
            )
            return game