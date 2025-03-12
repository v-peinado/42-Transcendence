"""
Shared state between consumers for game and player management
"""

# Dictionary of connected players: {user_id: {channel_name, username, last_seen}, ...}
connected_players = {}

# List of players waiting for a match: [{user, channel_name, join_time}, ...]
waiting_players = []

# Nested structure for players in games
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

# Stores GameState instances per game
# {game_id: GameState instance, ...}
game_states = {}

# Diagnostics
def get_status_snapshot():
    """Gets a snapshot of the current state for diagnostics"""
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