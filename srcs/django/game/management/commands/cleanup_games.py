from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from game.models import Game
from game.consumers.shared_state import game_players, connected_players, waiting_players

class Command(BaseCommand):
    help = 'Limpia el estado de partidas huérfanas o en estados inconsistentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo muestra lo que se haría pero no realiza cambios',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la limpieza incluso de partidas activas',
        )
        parser.add_argument(
            '--game-id',
            type=int,
            help='ID específico de partida a limpiar',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        specific_game_id = options.get('game_id')
        
        if dry_run:
            self.stdout.write("MODO SIMULACIÓN: No se realizarán cambios reales")
        
        self.stdout.write(self.style.SUCCESS("\n--- Estado Actual ---"))
        self.stdout.write(f"Jugadores conectados: {len(connected_players)}")
        self.stdout.write(f"Jugadores en espera: {len(waiting_players)}")
        self.stdout.write(f"Partidas activas en memoria: {len(game_players)}")
        
        # Mostrar partidas en estados inconsistentes
        if not specific_game_id:
            inconsistent_games = Game.objects.filter(
                status__in=['PLAYING', 'MATCHED', 'WAITING']
            ).exclude(
                started_at__gt=timezone.now() - timezone.timedelta(hours=3)
            )
            
            self.stdout.write(self.style.SUCCESS(f"\n--- Partidas Inconsistentes ({inconsistent_games.count()}) ---"))
            for game in inconsistent_games:
                self._print_game_info(game)
                
                if not dry_run and (force or self._should_cleanup_game(game)):
                    self._cleanup_game(game)
        else:
            # Limpiar una partida específica
            try:
                game = Game.objects.get(id=specific_game_id)
                self.stdout.write(self.style.SUCCESS(f"\n--- Partida {game.id} ---"))
                self._print_game_info(game)
                
                if not dry_run:
                    self._cleanup_game(game)
                    self.stdout.write(self.style.SUCCESS(f"Partida {game.id} limpiada"))
            except Game.DoesNotExist:
                raise CommandError(f'Partida con ID {specific_game_id} no existe')
        
        # Limpiar estructuras de memoria
        if not dry_run:
            # Limpiar partidas que ya no existen en la base de datos
            db_game_ids = set(str(id) for id in Game.objects.values_list('id', flat=True))
            memory_game_ids = set(game_players.keys())
            
            # Partidas en memoria que no están en la BD
            orphan_games = memory_game_ids - db_game_ids
            if orphan_games:
                self.stdout.write(self.style.SUCCESS(f"\n--- Limpiando {len(orphan_games)} partidas huérfanas ---"))
                for game_id in orphan_games:
                    if game_id in game_players:
                        del game_players[game_id]
                        self.stdout.write(f"Eliminada partida huérfana: {game_id}")
                    if game_id in game_states:
                        del game_states[game_id]
                        self.stdout.write(f"Eliminado estado de juego huérfano: {game_id}")
    
    def _print_game_info(self, game):
        """Muestra información detallada de una partida"""
        self.stdout.write(f"ID: {game.id} | Estado: {game.status}")
        self.stdout.write(f"  Creada: {game.created_at} | Iniciada: {game.started_at}")
        self.stdout.write(f"  Jugador 1: {game.player1.username if game.player1 else 'N/A'} (Ready: {game.player1_ready})")
        self.stdout.write(f"  Jugador 2: {game.player2.username if game.player2 else 'N/A'} (Ready: {game.player2_ready})")
        
        # Mostrar estado en memoria
        game_id_str = str(game.id)
        if game_id_str in game_players:
            self.stdout.write("  En memoria: Sí")
            for side, data in game_players[game_id_str].items():
                connected = data.get('connected', False) if data else False
                status = 'Conectado' if connected else 'Desconectado'
                user_id = data.get('user_id', 'N/A') if data else 'N/A'
                self.stdout.write(f"    {side.capitalize()}: {status} (ID: {user_id})")
        else:
            self.stdout.write("  En memoria: No")
    
    def _should_cleanup_game(self, game):
        """Determina si una partida debe ser limpiada automáticamente"""
        # Partidas en espera por más de 3 horas
        if game.status == 'WAITING' and game.created_at < timezone.now() - timezone.timedelta(hours=3):
            return True
        
        # Partidas emparejadas pero sin inicio por más de 1 hora
        if game.status == 'MATCHED' and game.created_at < timezone.now() - timezone.timedelta(hours=1):
            return True
            
        # Partidas en juego por más de 3 horas (probablemente abandonadas)
        if game.status == 'PLAYING' and game.created_at < timezone.now() - timezone.timedelta(hours=3):
            return True
            
        return False
    
    def _cleanup_game(self, game):
        """Limpia una partida marcándola como finalizada"""
        self.stdout.write(f"Limpiando partida {game.id}...")
        
        # Actualizar estado en base de datos
        game.status = 'FINISHED'
        game.finished_at = timezone.now()
        if not game.winner and game.player1:
            game.winner = game.player1  # Asignar ganador por defecto
        game.save()
        
        # Limpiar estado en memoria
        game_id_str = str(game.id)
        if game_id_str in game_players:
            del game_players[game_id_str]
        
        # También limpiar el estado del juego si existe
        if game_id_str in game_states:
            del game_states[game_id_str]
            
        self.stdout.write(self.style.SUCCESS(f"Partida {game.id} marcada como FINISHED"))
