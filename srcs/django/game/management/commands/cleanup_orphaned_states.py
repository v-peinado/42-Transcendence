from django.core.management.base import BaseCommand
from game.consumers.shared_state import game_states, game_players
import time

class Command(BaseCommand):
    help = 'Limpia estados de juego huérfanos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo muestra lo que se haría pero no realiza cambios',
        )
        
    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        # Mostrar información actual
        self.stdout.write(self.style.SUCCESS("=== Estado Actual ==="))
        self.stdout.write(f"Estados de juego en memoria: {len(game_states)}")
        self.stdout.write(f"Juegos con jugadores activos: {len(game_players)}")
        
        # Encontrar estados huérfanos (no tienen entrada en game_players)
        orphaned_states = []
        for game_id in list(game_states.keys()):
            if game_id not in game_players:
                orphaned_states.append(game_id)
                
        self.stdout.write(f"\nEstados huérfanos encontrados: {len(orphaned_states)}")
        
        # Limpiar estados huérfanos
        if orphaned_states and not dry_run:
            for game_id in orphaned_states:
                del game_states[game_id]
                self.stdout.write(f"Eliminado estado huérfano para juego {game_id}")
                
            self.stdout.write(self.style.SUCCESS(f"\nSe eliminaron {len(orphaned_states)} estados huérfanos"))
        elif orphaned_states:
            self.stdout.write(self.style.WARNING(f"\nModo simulación: se eliminarían {len(orphaned_states)} estados huérfanos"))
        else:
            self.stdout.write(self.style.SUCCESS("\nNo se encontraron estados huérfanos"))
