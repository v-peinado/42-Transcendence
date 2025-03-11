from ..utils.database_operations import DatabaseOperations
import asyncio
import time
import traceback

class MultiplayerHandler:
    """Handles multiplayer game logic"""
    
    @staticmethod
    async def handle_player_join(consumer, game):
        """Assign player to game side and mark player as ready to start"""
        try:
            # Check if this is a reconnection
            from ..shared_state import game_players
            game_id = str(game.id)
            is_reconnection = False
            
            if game_id in game_players:
                # Verify if player was previously connected
                player_data = None
                player_side = None
                
                for side, data in game_players[game_id].items():
                    if data and data.get('user_id') == consumer.user.id:
                        player_data = data
                        player_side = side
                        break
                        
                if player_data:
                    is_reconnection = True
                    consumer.side = player_side
                    game_players[game_id][player_side]['connected'] = True
                    game_players[game_id][player_side]['channel_name'] = consumer.channel_name
                    
                    # Resetear el estado de la pala para este jugador si estamos en medio de una partida
                    if hasattr(consumer, 'game_state') and consumer.game_state and consumer.game_state.status == 'playing':
                        # Obtener la posición actual y resetear estado de la pala
                        paddle = consumer.game_state.paddles.get(player_side)
                        if paddle:
                            print(f"Reseteando estado de pala para {consumer.user.username} ({player_side}) en reconexión")
                            paddle.reset_state()
                    
                    # Notify reconnection
                    await consumer.channel_layer.group_send(
                        consumer.room_group_name,
                        {
                            "type": "player_reconnected",
                            "player_id": consumer.user.id,
                            "side": player_side,
                            "username": consumer.user.username
                        }
                    )
                    return
            
            # Assign player to game side - Utilizamos los IDs directamente para evitar problemas async
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

            elif not game.player2_id:  # Si no hay player2 asignado
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
                print(f"Error: Player {consumer.user.username} could not join game {game.id}")
                return
            
            # Obtener el juego actualizado después de marcar jugador como listo
            updated_game = await DatabaseOperations.get_game(game.id)
            if not updated_game:
                print(f"Error: Could not get updated game {game.id}")
                return
                
            if (updated_game.player1_ready and updated_game.player2_ready and 
                updated_game.status != "PLAYING"):
                
                # Actualizar estado del juego a PLAYING
                updated_game = await DatabaseOperations.update_game_status(updated_game, "PLAYING")
                
                # Función auxiliar para obtener nombre con manejo de excepciones
                async def get_username_safe(user_id):
                    if not user_id:
                        return "Unknown"
                    from django.contrib.auth import get_user_model
                    from channels.db import database_sync_to_async
                    User = get_user_model()
                    
                    try:
                        user = await database_sync_to_async(User.objects.get)(id=user_id)
                        return user.username
                    except Exception:
                        return f"Player_{user_id}"
                
                # Obtener nombres de jugadores de forma segura
                player1_username = await get_username_safe(updated_game.player1_id)
                player2_username = await get_username_safe(updated_game.player2_id)
                
                # Enviar evento de inicio de juego
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
            print(f"[DEBUG] Error en handle_player_join: {error_details}")

    @staticmethod
    async def handle_player_disconnect(consumer):
        """Handle player disconnection (desertion)"""
        if consumer.game_state.status == "finished":	# if game is already finished,
            return
            
        if hasattr(consumer, "side"):	# if consumer has side attribute (is a player)
            from ..shared_state import game_players
            
            game_id = str(consumer.scope["game"].id)
            side = consumer.side
            
            # Mark player as disconnected
            if game_id in game_players and side in game_players[game_id] and game_players[game_id][side]:
                game_players[game_id][side]['connected'] = False
                
                # Verificar si ambos jugadores están desconectados
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
        from ..shared_state import game_players
        
        # wait for 30 seconds before checking if the player has reconnected
        await asyncio.sleep(30)
        
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
                        "reason": "timeout",
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
