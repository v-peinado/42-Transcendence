from dataclasses import dataclass, field
from typing import Dict, List, Optional
import asyncio
from datetime import datetime
from .game_state import GameState

@dataclass
class Player:
    id: int
    username: str
    ws_connection: object
    in_queue_since: datetime = field(default_factory=datetime.now)
    current_game: Optional[str] = None

@dataclass
class GameSession:
    id: str
    player1: Player
    player2: Player
    game_state: GameState
    status: str = 'waiting'  # waiting, playing, finished
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

class MatchmakingSystem:
    def __init__(self):
        self.queue: List[Player] = []
        self.active_games: Dict[str, GameSession] = {}
        
    async def add_to_queue(self, player_id: int, username: str, ws_connection) -> None:
        """Añade un jugador a la cola de matchmaking"""
        # Verificar si el jugador ya está en cola
        if any(p.id == player_id for p in self.queue):
            return
            
        # Verificar si el jugador ya está en una partida
        if any(game.player1.id == player_id or game.player2.id == player_id 
               for game in self.active_games.values()):
            return
            
        player = Player(id=player_id, username=username, ws_connection=ws_connection)
        self.queue.append(player)
        await self._try_match()
        
    async def _try_match(self) -> None:
        """Intenta emparejar jugadores en la cola"""
        if len(self.queue) >= 2:
            player1 = self.queue.pop(0)
            player2 = self.queue.pop(0)
            
            game_id = f"game_{player1.id}_{player2.id}_{datetime.now().timestamp()}"
            game_session = GameSession(
                id=game_id,
                player1=player1,
                player2=player2,
                game_state=GameState()
            )
            
            self.active_games[game_id] = game_session
            await self._notify_match_found(game_session)
            
    async def _notify_match_found(self, game: GameSession) -> None:
        """Notifica a los jugadores que se ha encontrado una partida"""
        match_data = {
            'type': 'match_found',
            'game_id': game.id,
            'opponent': {
                'player1': {
                    'id': game.player1.id,
                    'username': game.player1.username
                },
                'player2': {
                    'id': game.player2.id,
                    'username': game.player2.username
                }
            }
        }
        
        # Enviar notificación a ambos jugadores
        await game.player1.ws_connection.send_json(match_data)
        await game.player2.ws_connection.send_json(match_data)
        
    def remove_from_queue(self, player_id: int) -> None:
        """Elimina un jugador de la cola"""
        self.queue = [p for p in self.queue if p.id != player_id]
        
    def get_game_by_player(self, player_id: int) -> Optional[GameSession]:
        """Obtiene la partida actual de un jugador"""
        for game in self.active_games.values():
            if game.player1.id == player_id or game.player2.id == player_id:
                return game
        return None
        
    def end_game(self, game_id: str) -> None:
        """Finaliza una partida"""
        if game_id in self.active_games:
            game = self.active_games[game_id]
            game.status = 'finished'
            game.finished_at = datetime.now()