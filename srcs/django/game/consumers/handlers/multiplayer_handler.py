from ..utils.database_operations import DatabaseOperations
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from ..shared_state import game_players
import traceback
import asyncio
import time

class MultiplayerHandler:
    """Handles multiplayer game logic"""
    
    @staticmethod
    async def handle_player_join(consumer, game):
        """Assign player to game side and mark player as ready to start"""
        try:
        # Check if this is a reconnection
            game_id = str(game.id)	# get game id
            is_reconnection = False	# set reconnection flag
            
            # Verify if player was previously connected
            if game_id in game_players:	# if game_id is in game_players dictionary
                player_data = None	# set player data
                player_side = None
                
                for side, data in game_players[game_id].items(): # iterate over game_players[game_id]
                    if data and data.get('user_id') == consumer.user.id: # if data exists and user_id is the same as consumer.user.id
                        player_data = data	# fill player info
                        player_side = side
                        break	# break the loop
                        
                if player_data:	# if player_data exists
                    is_reconnection = True
                    consumer.side = player_side
                    game_players[game_id][player_side]['connected'] = True
                    game_players[game_id][player_side]['channel_name'] = consumer.channel_name
                    
                    # Reset paddle state for this player if we're in the middle of a game
                    if hasattr(consumer, 'game_state') and consumer.game_state and consumer.game_state.status == 'playing':
                        # Get current position and reset paddle state
                        paddle = consumer.game_state.paddles.get(player_side)
                        if paddle:             
							# Store current paddle speed before reset
                            current_speed = paddle.speed
                            # Reset paddle state
                            paddle.reset_state()
                            # Ensure we maintain the speed after reset
                            paddle.speed = current_speed
                            paddle.original_speed = current_speed if not hasattr(paddle, 'original_speed') else paddle.original_speed
                    
                    # Notify reconnection
                    await consumer.channel_layer.group_send(	# send message to group
                        consumer.room_group_name,
                        {
                            "type": "player_reconnected",
                            "player_id": consumer.user.id,
                            "side": player_side,
                            "username": consumer.user.username
                        }
                    )
                    return
            
        # Assign player to game side and mark player as ready to start
			# Player 1
            if game.player1_id and game.player1_id == consumer.user.id:
                consumer.side = "left"
                await DatabaseOperations.mark_player_ready(game, role="player1")
                
                # Register player in global registry if not already registered
                if game_id not in game_players:
                    game_players[game_id] = {"left": None, "right": None}
                game_players[game_id]["left"] = {
                    "user_id": consumer.user.id,
                    "connected": True,
                    "channel_name": consumer.channel_name
                }
            # Player 2    
            elif game.player2_id and game.player2_id == consumer.user.id:
                consumer.side = "right"
                await DatabaseOperations.mark_player_ready(game, role="player2")
                
                # Register player in global registry if not already registered
                if game_id not in game_players:
                    game_players[game_id] = {"left": None, "right": None}
                game_players[game_id]["right"] = {
                    "user_id": consumer.user.id,
                    "connected": True,
                    "channel_name": consumer.channel_name
                }

            elif not game.player2_id:
                consumer.side = "right"
                await DatabaseOperations.set_player2(game, consumer.user)
                await DatabaseOperations.mark_player_ready(game, role="player2")
                
                # Register player in global registry if not already registered
                if game_id not in game_players:
                    game_players[game_id] = {"left": None, "right": None}
                game_players[game_id]["right"] = {
                    "user_id": consumer.user.id,
                    "connected": True,
                    "channel_name": consumer.channel_name
                }
            else:
                print(f"Error: Player {consumer.user.username} could not join game {game.id}")	# player not found
                return
            
            # Obtaining updated game state to check if both players are ready
            updated_game = await DatabaseOperations.get_game(game.id)
            if not updated_game:
                print(f"Error: Could not get updated game {game.id}")
                return
                
            if (updated_game.player1_ready and updated_game.player2_ready and 
                updated_game.status != "PLAYING"):
                
                # Set game status to PLAYING
                updated_game = await DatabaseOperations.update_game_status(updated_game, "PLAYING")
                
                # Auxiliar function to get player username safely
                async def get_username_safe(user_id):
                    """Get player username safely from user id"""
                    if not user_id:	# if user_id is not defined
                        return "Unknown" # we parse "Unknown"

                    User = get_user_model()	
                    
                    try:
                        user = await database_sync_to_async(User.objects.get)(id=user_id)
                        return user.username
                    except Exception:
                        return f"Player_{user_id}"
                
                # Get player usernames for game start event
                player1_username = await get_username_safe(updated_game.player1_id)
                player2_username = await get_username_safe(updated_game.player2_id)
                
                # Send game start event to both players
                await consumer.channel_layer.group_send(
                    consumer.room_group_name,
                    {
                        "type": "game_start",
                        "player1": player1_username,
                        "player2": player2_username,
                        "player1_id": updated_game.player1_id,
                        "player2_id": updated_game.player2_id,
                        "game_id": updated_game.id,
                    },
                )
                
                # Start game countdown
                consumer.game_state.status = "countdown"
                await consumer.game_state.start_countdown()
                asyncio.create_task(consumer.game_loop())
        except Exception as e:
            error_details = traceback.format_exc()
            print(f"[DEBUG] Error en handle_player_join: {error_details}") # in case of error, print the error details

    @staticmethod
    async def handle_player_disconnect(consumer):
        """Handle player disconnection"""
        if consumer.game_state.status == "finished":	# if game is already finished,
            return
            
        if hasattr(consumer, "side"):	# if consumer has side attribute (is a player)
            
            game_id = str(consumer.scope["game"].id) # get game id
            side = consumer.side # get side
            
            # Mark player as disconnected
            if game_id in game_players and side in game_players[game_id] and game_players[game_id][side]:
                game_players[game_id][side]['connected'] = False
                
                # Check if both players are disconnected
                both_disconnected = all(not player_data.get('connected', False) 
                                      for player_data in game_players[game_id].values() 
                                      if player_data is not None)
                
                if both_disconnected:
                    # If both players are disconnected, finish the game
                    consumer.game_state.status = "finished"
                    game = consumer.scope["game"]
                    await DatabaseOperations.update_game_status(game, "FINISHED")
                    
                    # Clear game record
                    del game_players[game_id]
                    
                    await consumer.channel_layer.group_send(
                        consumer.room_group_name,
                        {
                            "type": "game_finished",
                            "winner": None,
                            "reason": "abandonment",
                            "final_score": {
                                "left": consumer.game_state.paddles["left"].score,
                                "right": consumer.game_state.paddles["right"].score,
                            },
                        },
                    )
                else:
                    # Notify the other player of the disconnection event
                    await consumer.channel_layer.group_send(
                        consumer.room_group_name,
                        {
                            "type": "player_disconnected",
                            "side": side,
                            "player_id": consumer.user.id
                        },
                    )
                    
                    # time out the player for reconnection
                    game_players[game_id][side]['disconnect_time'] = time.time()
                    
                    # Initiate reconnection timeout handler
                    asyncio.create_task(
                        MultiplayerHandler.handle_reconnect_timeout(
                            consumer.channel_layer, 
                            consumer.room_group_name,
                            game_id, 
                            side,
                            consumer.game_state,
                            consumer.scope["game"]
                        )
                    )
    
    @staticmethod
    async def handle_reconnect_timeout(channel_layer, room_group_name, game_id, side, game_state, game):
        
        await asyncio.sleep(30) # <<< wait n seconds before checking if the player has reconnected
        
        # If the player has not reconnected, end the game
        if (game_id in game_players and 
            side in game_players[game_id] and 
            game_players[game_id][side] and 
            not game_players[game_id][side].get('connected', False)):
            
            # Verify if the game is still active
            if game_state.status != "finished":
                # Determine the winner 
                winner_side = "right" if side == "left" else "left"
                
                # Actualize game state
                game_state.status = "finished"
                await DatabaseOperations.update_game_on_disconnect(game, side)
                
                # Notify end of game
                await channel_layer.group_send(
                    room_group_name,
                    {
                        "type": "game_finished",
                        "winner": winner_side,
                        "reason": "timeout",	# reason for game end is timeout
                        "timeout_side": side,
                        "final_score": {
                            "left": game_state.paddles["left"].score,
                            "right": game_state.paddles["right"].score,
                        },
                    },
                )
                
                # Clear game record from global registry
                if game_id in game_players:
                    del game_players[game_id]
