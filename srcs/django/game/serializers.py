from django.core.serializers import serialize
import json
from .models import Game
from django.contrib.auth import get_user_model

User = get_user_model()

def serialize_user(user):
    """User serializer for game"""
    return {
        'id': user.id,
        'username': user.username
    }

def serialize_game(game):
    """Game serializer"""
    data = json.loads(serialize('json', [game]))[0]['fields']
    
    # Add related user data
    if game.player1:
        data['player1'] = serialize_user(game.player1)
    if game.player2:
        data['player2'] = serialize_user(game.player2)
    if game.winner:
        data['winner'] = serialize_user(game.winner)
        
    # Add id to the serialized data
    data['id'] = game.id
        
    return data
