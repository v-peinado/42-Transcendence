import { loadHTML } from '../../utils/htmlLoader.js';
import { soundService } from '../../services/SoundService.js';
import AuthService from '../../services/AuthService.js';
import TournamentService from '../../services/TournamentService.js';
import { getNavbarHTML } from '../../components/Navbar.js';
import { TournamentGame } from '../game/components/TournamentGame.js';
import GameModalService from '../../services/GameModalService.js';

export async function TournamentGameView(tournamentId, matchId) {
    const app = document.getElementById('app');
    
    try {
        // Cargar template y datos necesarios
        const [template, userInfo, matchInfo] = await Promise.all([
            loadHTML('/views/game/templates/GameMatch.html'),
            AuthService.getUserProfile(),
            TournamentService.getMatchInfo(tournamentId, matchId)
        ]);

        // Configurar la vista
        app.innerHTML = await getNavbarHTML(true, userInfo);
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = template;
        app.appendChild(tempDiv.firstElementChild);

        // Cargar CSS si es necesario
        if (!document.querySelector('link[href="/css/game.css"]')) {
            const linkElem = document.createElement('link');
            linkElem.rel = 'stylesheet';
            linkElem.href = '/css/game.css';
            document.head.appendChild(linkElem);
        }

        // Configurar jugadores
        document.querySelector('#leftPlayerName').textContent = matchInfo.player1.username;
        // Esperar a que el DOM esté listo
        await new Promise(requestAnimationFrame);

        // Mostrar modal de partida encontrada
        const matchFoundModal = document.getElementById('matchFoundModal');
        matchFoundModal.style.display = 'flex';

        // Iniciar secuencia de juego
        setTimeout(async () => {
            matchFoundModal.style.display = 'none';
            
            // Cuenta regresiva
            const countdown = document.getElementById('countdown');
            countdown.style.display = 'flex';
            
            for(let i = 3; i >= 1; i--) {
                countdown.textContent = i;
                countdown.classList.add('countdown-pulse');
                soundService.playCountdown();
                await new Promise(r => setTimeout(r, 1000));
            }
            
            countdown.textContent = 'GO!';
            soundService.playCountdown();
            await new Promise(r => setTimeout(r, 1000));
            countdown.style.display = 'none';

            // Configurar y empezar el juego
            const canvas = document.getElementById('gameCanvas');
            const game = new TournamentGame(
                canvas,
                matchInfo,
                matchInfo.tournament.max_match_points,
                async (player1Points, player2Points, winner) => {
                    game.stop();
                    const winnerId = winner === 'Player1' ? matchInfo.player1.id : matchInfo.player2.id;
                    
                    try {
                        const result = await TournamentService.updateMatchResult(tournamentId, matchId, {
                            player1_points: player1Points,
                            player2_points: player2Points,
                            winner: winnerId
                        });
                        
                        await handleGameEnd(player1Points, player2Points, winner, matchInfo, result);
                    } catch (error) {
                        console.error('Error al finalizar la partida:', error);
                        window.location.href = '/tournament/local';
                    }
                }
            );
            game.start();
        }, 2000);

    } catch (error) {
        console.error('Error al cargar la partida del torneo:', error);
        window.location.href = '/tournament/local';
    }
}

async function showResultModal(result, match, tournament, player1Points, player2Points, winner) {
    try {
        GameModalService.showGameOver({
            final_score: {
                left: player1Points,
                right: player2Points
            },
            winner: winner === 'Player1' ? 'left' : 'right',
            playerSide: winner === 'Player1' ? 'left' : 'right', // Corregir esto
            returnUrl: result.next_match ? 
                `/tournament/game/${tournament.id}/${result.next_match.id}` : 
                '/tournament/local',
            returnText: result.next_match ? 
                '<i class="fas fa-play me-2"></i>Siguiente Partido' : 
                '<i class="fas fa-home me-2"></i>Volver al Menú',
            nextMatch: result.next_match ? 
                `${result.next_match.player1.username} vs ${result.next_match.player2.username}` : 
                null,
            isTournament: true // Añadir esta bandera
        });

        if (winner === 'Player1') {
            soundService.playVictory();
        } else {
            soundService.playDefeat();
        }
    } catch (error) {
        console.error('Error al mostrar resultado:', error);
        window.location.href = '/tournament/local';
    }
}

async function handleGameEnd(player1Points, player2Points, winner, matchInfo, result) {
    try {
        GameModalService.showGameOver({
            final_score: {
                left: player1Points,
                right: player2Points
            },
            winner: winner === 'Player1' ? 'left' : 'right',
            playerSide: winner === 'Player1' ? 'left' : 'right',
            returnUrl: result.next_match ? 
                `/tournament/game/${tournamentId}/${result.next_match.id}` : 
                '/tournament/local',
            returnText: result.next_match ? 
                '<i class="fas fa-play me-2"></i>Siguiente Partido' : 
                '<i class="fas fa-home me-2"></i>Volver al Menú',
            nextMatch: result.next_match ? 
                `${result.next_match.player1.username} vs ${result.next_match.player2.username}` : null,
            isTournament: true,
            player1Name: matchInfo.player1.username,
            player2Name: matchInfo.player2.username
        });

        if (winner === 'Player1') {
            soundService.playVictory();
        } else {
            soundService.playDefeat();
        }
    } catch (error) {
        console.error('Error al mostrar resultado:', error);
        window.location.href = '/tournament/local';
    }
}
