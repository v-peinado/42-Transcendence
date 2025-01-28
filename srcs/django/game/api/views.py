from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from ..models import Game
from ..engine.game_state import GameState
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .serializers import GameSerializer
from django.utils import timezone
from ..engine.matchmaking import MatchmakingSystem

@login_required
def create_game(request):
    """Crea una nueva partida y devuelve su ID"""
    game = Game.objects.create(
        player1=request.user,
        status='WAITING'
    )
    return JsonResponse({
        'game_id': game.id,
        'status': 'created'
    })

@login_required
def join_game(request, game_id):
    """Une a un jugador a una partida existente"""
    try:
        game = Game.objects.get(id=game_id, status='WAITING')
        if game.player1 != request.user and not game.player2:
            game.player2 = request.user
            game.status = 'PLAYING'
            game.save()
            
            # Notificar a través de WebSocket que el juego puede comenzar
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'game_{game_id}',
                {
                    'type': 'game_start',
                    'game_id': game_id,
                    'player1': game.player1.username,
                    'player2': game.player2.username
                }
            )
            
            return JsonResponse({
                'status': 'joined',
                'game_id': game_id
            })
    except Game.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Game not found or already full'
        }, status=404)

@login_required
def game_status(request, game_id):
    """Obtiene el estado actual de una partida"""
    try:
        game = Game.objects.get(id=game_id)
        return JsonResponse({
            'status': game.status,
            'player1': game.player1.username,
            'player2': game.player2.username if game.player2 else None,
            'score_player1': game.score_player1,
            'score_player2': game.score_player2
        })
    except Game.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Game not found'
        }, status=404)

@login_required
def game_page(request, game_id=None):
    """Renderiza la página del juego"""
    return render(request, 'game/game.html', {
        'game_id': game_id,
        'user_id': request.user.id,
        'username': request.user.username
    })

class GameViewSet(viewsets.ModelViewSet):
    serializer_class = GameSerializer
    permission_classes = [IsAuthenticated]
    matchmaking = MatchmakingSystem()

    def get_queryset(self):
        return Game.objects.filter(
            player1=self.request.user
        ) | Game.objects.filter(
            player2=self.request.user
        ).order_by('-created_at')

    @action(detail=False, methods=['post'])
    def create_game(self, request):
        """Crea una nueva partida"""
        game = Game.objects.create(
            player1=request.user,
            status='WAITING'
        )
        serializer = self.get_serializer(game)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def join_game(self, request, pk=None):
        """Une a un jugador a una partida existente"""
        game = self.get_object()
        if game.status != 'WAITING' or game.player2:
            return Response(
                {'error': 'Game not available'},
                status=status.HTTP_400_BAD_REQUEST
            )

        game.player2 = request.user
        game.status = 'PLAYING'
        game.save()

        # Notificar vía WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'game_{game.id}',
            {
                'type': 'game_start',
                'game_id': game.id,
                'player1': game.player1.username,
                'player2': game.player2.username
            }
        )
        
        serializer = self.get_serializer(game)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def join_queue(self, request):
        """Une al usuario a la cola de matchmaking"""
        try:
            # Verificar si ya está en una partida
            if Game.objects.filter(
                status='PLAYING',
                finished_at__isnull=True
            ).filter(player1=request.user).exists() or Game.objects.filter(
                status='PLAYING',
                finished_at__isnull=True
            ).filter(player2=request.user).exists():
                return Response(
                    {'error': 'Ya estás en una partida'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            self.matchmaking.add_to_queue(
                player_id=request.user.id,
                username=request.user.username,
                ws_connection=None
            )
            return Response({'status': 'added_to_queue'})
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def forfeit(self, request, pk=None):
        """Abandona la partida actual"""
        game = self.get_object()
        if game.status != 'PLAYING':
            return Response(
                {'error': 'La partida no está en curso'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.user == game.player1:
            game.score_player2 = 10
            game.score_player1 = 0
            winner = game.player2
        else:
            game.score_player1 = 10
            game.score_player2 = 0
            winner = game.player1

        game.status = 'FINISHED'
        game.finished_at = timezone.now()
        game.winner = winner
        game.save()

        return Response({'status': 'game_forfeited'})

    @action(detail=True, methods=['get'])
    def game_state(self, request, pk=None):
        """Obtiene el estado actual de una partida"""
        game = self.get_object()
        game_state = self.matchmaking.get_game_state(game.id)
        
        if not game_state:
            return Response(
                {'error': 'Estado de juego no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
            
        return Response(game_state.serialize())

    def game_page(self, request, game_id=None):
        """Renderiza la página del juego"""
        return render(request, 'game/game.html', {
            'game_id': game_id,
            'user_id': request.user.id,
            'username': request.user.username
        })