from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import Game

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'profile_image']

class GameSerializer(serializers.ModelSerializer):
    player1 = UserSerializer(read_only=True)
    player2 = UserSerializer(read_only=True)
    winner = UserSerializer(read_only=True)
    status_display = serializers.SerializerMethodField()
    can_join = serializers.SerializerMethodField()
    is_player = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = [
            'id',
            'player1',
            'player2',
            'score_player1',
            'score_player2',
            'status',
            'status_display',
            'created_at',
            'started_at',
            'finished_at',
            'winner',
            'can_join',
            'is_player'
        ]

    def get_status_display(self, obj):
        """Devuelve una versión legible del estado del juego"""
        status_map = {
            'WAITING': 'Esperando jugadores',
            'PLAYING': 'En curso',
            'FINISHED': 'Finalizado',
            'CANCELLED': 'Cancelado'
        }
        return status_map.get(obj.status, obj.status)

    def get_can_join(self, obj):
        """Determina si el usuario actual puede unirse a la partida"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        # Solo se puede unir si:
        # 1. La partida está en espera
        # 2. No es el creador
        # 3. No hay segundo jugador
        return (
            obj.status == 'WAITING' and
            obj.player1 != request.user and
            obj.player2 is None
        )

    def get_is_player(self, obj):
        """Determina si el usuario actual es un jugador de la partida"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        return request.user in [obj.player1, obj.player2]

class GameStateSerializer(serializers.Serializer):
    """Serializer para el estado actual del juego"""
    ball = serializers.DictField()
    paddles = serializers.DictField()
    score = serializers.DictField()
    status = serializers.CharField()
    canvas = serializers.DictField()
    timestamp = serializers.DateTimeField()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Añadir datos adicionales si es necesario
        return data