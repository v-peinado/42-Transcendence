# from django.http import JsonResponse
# from django.views import View
# from django.contrib.auth.mixins import LoginRequiredMixin
# from ..models import Game

# class GameVerificationAPI(LoginRequiredMixin, View):
#     """API endpoint para verificar la existencia y acceso de una partida"""
    
#     def get(self, request, game_id):
#         """Verifica si una partida existe y el usuario tiene acceso a ella"""
#         try:
#             # Verificar si la partida existe en la base de datos
#             game_exists = Game.objects.filter(id=game_id).exists()
            
#             # Si no existe, devolver falso
#             if not game_exists:
#                 return JsonResponse({
#                     'exists': False,
#                     'can_access': False,
#                     'message': 'Partida no encontrada'
#                 }, status=404)
            
#             # Obtener la partida
#             game = Game.objects.get(id=game_id)
            
#             # Verificar si el usuario es jugador de la partida
#             user_is_player = (game.player1_id == request.user.id or 
#                              (game.player2_id is not None and game.player2_id == request.user.id))
            
#             # Verificar si la partida está en curso o finalizada
#             game_is_finished = game.status == 'FINISHED'
            
#             # Verificar conexiones activas
#             active_game_connections = False
#             from ..consumers.shared_state import game_players
#             if str(game_id) in game_players:
#                 # Hay al menos una conexión activa en esta partida
#                 active_connections = any(
#                     data and data.get('connected', False) 
#                     for data in game_players[str(game_id)].values()
#                 )
#                 active_game_connections = active_connections
            
#             # Construir respuesta detallada
#             return JsonResponse({
#                 'exists': True,
#                 'can_access': user_is_player and not game_is_finished,
#                 'status': game.status,
#                 'is_player': user_is_player,
#                 'is_finished': game_is_finished,
#                 'active_connections': active_game_connections,
#                 'message': self._build_status_message(game, user_is_player, game_is_finished)
#             })
            
#         except Exception as e:
#             # En caso de error, devolver error
#             return JsonResponse({
#                 'exists': False,
#                 'can_access': False,
#                 'message': f'Error verificando partida: {str(e)}'
#             }, status=500)
    
#     def _build_status_message(self, game, is_player, is_finished):
#         """Genera un mensaje descriptivo sobre el estado de la partida"""
#         if is_finished:
#             return "Esta partida ya ha finalizado."
        
#         if not is_player:
#             return "No tienes acceso a esta partida."
        
#         if game.status == 'WAITING':
#             return "Partida en espera de jugadores."
#         elif game.status == 'MATCHED':
#             return "Partida emparejada, esperando inicio."
#         elif game.status == 'PLAYING':
#             return "Partida en curso."
            
#         return "Estado desconocido."
