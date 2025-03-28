import { loadHTML } from '../../utils/htmlLoader.js';
import { soundService } from '../../services/SoundService.js';
import AuthService from '../../services/AuthService.js';
import { getNavbarHTML } from '../../components/Navbar.js';
import { SinglePlayerGame } from './components/SinglePlayerGame.js';
import { showGameOverModal, hideGameOverModal } from '../../components/GameOverModal.js';
import { DIFFICULTY_LEVELS } from '../../config/GameConfig.js';

export async function SinglePlayerGameView() {
    const app = document.getElementById('app');
    
    const [template, userInfo, modalHtml] = await Promise.all([
        loadHTML('/views/game/templates/GameMatch.html'),
        AuthService.getUserProfile(),
        loadHTML('/views/game/templates/modals/GameOverModal.html')
    ]);

    // Obtener el navbar procesado y añadirlo
    const navbarHtml = await getNavbarHTML(true, userInfo);
    
    // Insertar el modal antes que cualquier otra cosa
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Verificar que el modal y sus elementos existen
    const gameOverScreen = document.getElementById('gameOverScreen');
    if (!gameOverScreen) {
        console.error('Error: Modal no encontrado');
        return;
    }

    // Preparar el contenido y añadirlo al DOM
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = template;
    app.innerHTML = navbarHtml;
    app.appendChild(tempDiv.firstElementChild);

    // Esperar al siguiente frame para asegurar que el DOM está actualizado
    await new Promise(requestAnimationFrame);

    // Configurar fullscreen (SOLO AQUÍ, eliminar la otra configuración)
    const gameWrapper = document.querySelector('.game-wrapper');
    const fullscreenBtn = document.getElementById('fullscreenBtn');

    if (fullscreenBtn && gameWrapper) {
        fullscreenBtn.onclick = () => {
            try {
                if (!document.fullscreenElement) {
                    if (gameWrapper.requestFullscreen) {
                        gameWrapper.requestFullscreen();
                    } else if (gameWrapper.webkitRequestFullscreen) {
                        gameWrapper.webkitRequestFullscreen();
                    } else if (gameWrapper.msRequestFullscreen) {
                        gameWrapper.msRequestFullscreen();
                    }
                } else {
                    if (document.exitFullscreen) {
                        document.exitFullscreen();
                    } else if (document.webkitExitFullscreen) {
                        document.webkitExitFullscreen();
                    } else if (document.msExitFullscreen) {
                        document.msExitFullscreen();
                    }
                }
            } catch (err) {
                console.error('Error con fullscreen:', err);
            }
        };

        const handleFullscreenChange = () => {
            if (document.fullscreenElement) {
                fullscreenBtn.innerHTML = '<i class="fas fa-compress"></i>';
                gameWrapper.classList.add('fullscreen');
            } else {
                fullscreenBtn.innerHTML = '<i class="fas fa-expand"></i>';
                gameWrapper.classList.remove('fullscreen');
            }
        };

        document.addEventListener('fullscreenchange', handleFullscreenChange);
        document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
        document.addEventListener('mozfullscreenchange', handleFullscreenChange);
        document.addEventListener('MSFullscreenChange', handleFullscreenChange);
    }

    // Actualizar nombres de jugadores y avatares
    document.querySelector('#leftPlayerName').textContent = userInfo.username;
    document.querySelector('#rightPlayerName').textContent = 'CPU';

    // Actualizar avatar del jugador con la imagen del perfil o la imagen de 42
    const player1Avatar = document.querySelector('.player-card:first-child .player-avatar');
    if (player1Avatar) {
        if (userInfo.profile_image) {
            player1Avatar.innerHTML = `<img src="${userInfo.profile_image}" alt="${userInfo.username}" />`;
        } else if (userInfo.fortytwo_image) {
            player1Avatar.innerHTML = `<img src="${userInfo.fortytwo_image}" alt="${userInfo.username}" />`;
        }
    }

    // Cambiar el icono del CPU a robot
    const player2Avatar = document.querySelector('.player-card:last-child .player-avatar i');
    if (player2Avatar) {
        player2Avatar.className = 'fas fa-robot';
    }

    // También actualizar el avatar en la pantalla de fin de juego
    const finalPlayer1Avatar = document.querySelector('.player-column:first-child .player-avatar');
    if (finalPlayer1Avatar) {
        if (userInfo.profile_image) {
            finalPlayer1Avatar.innerHTML = `<img src="${userInfo.profile_image}" alt="${userInfo.username}" />`;
        } else if (userInfo.fortytwo_image) {
            finalPlayer1Avatar.innerHTML = `<img src="${userInfo.fortytwo_image}" alt="${userInfo.username}" />`;
        }
    }

    // Ocultar la pantalla de game over al inicio
    if (gameOverScreen) {
        gameOverScreen.style.display = 'none';
    }

    // Iniciar secuencia del juego
    const difficultyModal = document.getElementById('difficultyModal');
    difficultyModal.style.display = 'flex';

    await new Promise(resolve => {
        const difficultyCards = document.querySelectorAll('.game-mode-card');
        difficultyCards.forEach(card => {
            card.onclick = () => {
                difficultyCards.forEach(c => c.classList.remove('active'));
                card.classList.add('active');
                
                difficultyModal.style.display = 'none';
                resolve({
                    difficulty: card.dataset.difficulty
                });
            };
        });
    }).then(async (difficultySettings) => {
        // Mostrar cuenta regresiva
        const countdown = document.getElementById('countdown');
        countdown.style.display = 'flex';
        
        // Remover elementos del matchFound si existen
        const matchFoundModal = document.getElementById('matchFoundModal');
        if (matchFoundModal) {
            matchFoundModal.remove(); // Eliminamos completamente el elemento
        }
        
        // Cuenta regresiva con sonido
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

        // Iniciar juego con la dificultad seleccionada
        startGame(difficultySettings);
    });

    // Eliminar duplicación del gameOverScreen
    if (gameOverScreen) {
        gameOverScreen.style.cssText = 'display: none; opacity: 0; visibility: hidden;';
        console.log('Modal inicializado correctamente');
    }

    function startGame(difficultySettings) {
        const canvas = document.getElementById('gameCanvas');
        if (!canvas) {
            console.error('Canvas no encontrado');
            return;
        }

        // Limpiar completamente el canvas
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        canvas.width = 1000;
        canvas.height = 600;

        // Reiniciar scores
        document.getElementById('player1Score').textContent = '0';
        document.getElementById('player2Score').textContent = '0';

        // Crear nueva instancia del juego
        const game = new SinglePlayerGame(canvas, difficultySettings.difficulty, 5, 
            (winner) => {
                console.log('Juego terminado, mostrando modal...');
                const finalScore = {
                    player1: parseInt(document.getElementById('player1Score').textContent),
                    player2: parseInt(document.getElementById('player2Score').textContent)
                };

                showGameOverModal(
                    winner === 'player1' ? userInfo.username : 'CPU',
                    {
                        username: userInfo.username,
                        profile_image: userInfo.profile_image,
                        fortytwo_image: userInfo.fortytwo_image
                    },
                    {
                        username: 'CPU',
                        is_cpu: true
                    },
                    finalScore,
                    {
                        customButton: {
                            text: 'Jugar de Nuevo',
                            icon: 'fas fa-redo',
                            onClick: () => {
                                hideGameOverModal();
                                // Forzar una recarga completa de la vista
                                window.location.reload();
                            }
                        }
                    }
                );
            }
        );

        game.start();
    }
}
