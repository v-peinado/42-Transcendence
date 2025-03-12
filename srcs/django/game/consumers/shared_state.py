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
