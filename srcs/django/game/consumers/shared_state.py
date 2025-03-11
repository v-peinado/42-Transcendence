"""
Estado compartido entre consumidores para la gestión de partidas y jugadores
"""

# Diccionario de jugadores conectados: {user_id: {channel_name, username, last_seen}, ...}
connected_players = {}

# Lista de jugadores en espera de partida: [{user, channel_name, join_time}, ...]
waiting_players = []

# Estructura anidada para jugadores en partidas
# {
#   game_id: {
#     "left": {
#       "user_id": id,
#       "connected": bool,
#       "channel_name": name,
#       "disconnect_time": timestamp,
#     },
#     "right": {
#       "user_id": id, 
#       "connected": bool,
#       "channel_name": name,
#       "disconnect_time": timestamp,
#     }
#   }
# }
game_players = {}

# Almacena las instancias de GameState por partida
# {game_id: GameState instance, ...}
game_states = {}

# Diagnostics
def get_status_snapshot():
    """Obtiene un snapshot del estado actual para diagnóstico"""
    return {
        "connected_count": len(connected_players),
        "waiting_count": len(waiting_players),
        "active_games": len(game_players),
        "game_states": len(game_states),
        "game_players_details": {
            game_id: {
                side: {
                    "user_id": data["user_id"],
                    "connected": data["connected"],
                    "disconnect_time": data.get("disconnect_time")
                } if data else None
                for side, data in sides.items()
            }
            for game_id, sides in game_players.items()
        }
    }