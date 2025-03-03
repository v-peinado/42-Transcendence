import { loadHTML } from '../../utils/htmlLoader.js';
import { soundService } from '../../services/SoundService.js';

export async function GameMatchView(gameId) {
    console.log('Iniciando partida:', gameId);
    const app = document.getElementById('app');
    
    // Cargar template y CSS
    const template = await loadHTML('/views/game/templates/GameMatch.html');
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = template;
    
    // Limpiar y añadir el nuevo contenido
    app.innerHTML = '';
    app.appendChild(tempDiv.firstElementChild);

    // Cargar CSS
    if (!document.querySelector('link[href="/css/game.css"]')) {
        const linkElem = document.createElement('link');
        linkElem.rel = 'stylesheet';
        linkElem.href = '/css/game.css';
        document.head.appendChild(linkElem);
    }

    // Variables de estado
    let playerSide = null;
    let gameState = null;
    let activeKeys = new Set();
    let movementInterval = null;
    const userId = localStorage.getItem('user_id');
    
    console.log('User ID en juego:', userId);  // Debug user_id

    // Setup canvas y contexto
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    canvas.width = 1000;
    canvas.height = 600;

    // Conexión WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/game/${gameId}/`;
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        console.log('Conexión establecida');
        document.getElementById('gameStatus').textContent = '🎮 Conectado - Esperando oponente...';
    };

    async function showPreMatchSequence(player1, player2, playerSide) {
        return new Promise(async (resolve) => {
            const modal = document.getElementById('matchFoundModal');
            const countdown = document.getElementById('countdown');
                
            // 1. Mostrar modal inicial
            document.getElementById('player1NamePreMatch').textContent = player1;
            document.getElementById('player2NamePreMatch').textContent = player2;
            document.getElementById('playerControls').textContent = 
                playerSide === 'left' ? 'W / S' : '↑ / ↓';
                
            modal.style.display = 'flex';
            await new Promise(r => setTimeout(r, 2000));
                
            // 2. Ocultar modal
            modal.style.animation = 'fadeOut 0.5s ease-out';
            await new Promise(r => setTimeout(r, 500));
            modal.style.display = 'none';
                
            // 3. Mostrar cuenta regresiva
            for(let i = 3; i >= 0; i--) {
                countdown.style.display = 'flex';
                countdown.textContent = i === 0 ? 'GO!' : i.toString();
                countdown.classList.remove('countdown-pulse');
                void countdown.offsetWidth;
                countdown.classList.add('countdown-pulse');
                await soundService.playCountdown();
                await new Promise(r => setTimeout(r, 1000));
            }
            countdown.style.display = 'none';
                
            resolve();
        });
    }

    let gameStarted = false; // Nueva variable de estado

    socket.onmessage = async (event) => {
        const data = JSON.parse(event.data);
        console.log('Mensaje recibido:', data); // Debug
        
        switch(data.type) {
            case 'game_start':
                console.log('Game Start Data:', data);
                
                // Actualizar nombres en todos los lugares necesarios
                document.querySelector('#player1NamePreMatch').textContent = data.player1;
                document.querySelector('#player2NamePreMatch').textContent = data.player2;
                document.querySelector('#leftPlayerName').textContent = data.player1;
                document.querySelector('#rightPlayerName').textContent = data.player2;

                // Asignar lado del jugador
                if (userId === data.player1_id.toString()) {
                    playerSide = 'left';
                } else if (userId === data.player2_id.toString()) {
                    playerSide = 'right';
                }

                await showPreMatchSequence(data.player1, data.player2, playerSide);
                setupControls();
                gameStarted = true;
                
                socket.send(JSON.stringify({
                    type: 'start_game',
                    game_id: gameId
                }));
                break;

            case 'game_state':
                // Simplificar la lógica de cuando procesar estados
                if (gameStarted) {
                    handleGameState(data.state);
                }
                break;

            case 'game_finished':
                handleGameEnd(data);
                break;
        }
    };

    function handleGameStart(data) {
        console.log('Game Start:', {
            player1_id: data.player1_id,
            player2_id: data.player2_id,
            myId: userId
        });

        // Asignar lado y actualizar UI
        if (userId === data.player1_id.toString()) {
            playerSide = 'left';
            document.getElementById('playerInfo').textContent = `Tú eres el Jugador 1 (${data.player1})`;
            document.getElementById('controlsInfo').textContent = 'Controles: W/S para arriba/abajo';
        } else if (userId === data.player2_id.toString()) {
            playerSide = 'right';
            document.getElementById('playerInfo').textContent = `Tú eres el Jugador 2 (${data.player2})`;
            document.getElementById('controlsInfo').textContent = 'Controles: ↑/↓ para arriba/abajo';
        }

        document.getElementById('gameStatus').textContent = '¡Partida iniciada!';
        setupControls();
    }

    function handleGameState(state) {
        // No necesitamos la comprobación de gameStarted aquí ya que lo hacemos arriba
        gameState = state;
        requestAnimationFrame(drawGame);

        // Actualizar marcador
        document.getElementById('player1Score').textContent = state.paddles.left.score;
        document.getElementById('player2Score').textContent = state.paddles.right.score;
    }

    function drawGame() {
        if (!gameState) return;

        // Fondo limpio y elegante
        ctx.fillStyle = 'rgba(16, 19, 34, 0.95)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Línea central sutil
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
        ctx.lineWidth = 2;
        ctx.setLineDash([10, 10]);
        ctx.beginPath();
        ctx.moveTo(canvas.width / 2, 0);
        ctx.lineTo(canvas.width / 2, canvas.height);
        ctx.stroke();
        ctx.setLineDash([]);

        // Dibujar raquetas con estilo minimalista
        ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
        Object.values(gameState.paddles).forEach(paddle => {
            ctx.beginPath();
            ctx.roundRect(paddle.x, paddle.y, paddle.width, paddle.height, 5);
            ctx.fill();
        });

        // Dibujar pelota con brillo sutil
        ctx.beginPath();
        ctx.arc(gameState.ball.x, gameState.ball.y, gameState.ball.radius, 0, Math.PI * 2);
        ctx.fill();
    }

    function handleGameEnd(data) {
        const gameOverScreen = document.getElementById('gameOverScreen');
        const winnerText = document.getElementById('winnerText');
        const resultIcon = document.querySelector('.result-icon i');
        const player1Score = document.querySelector('.player1-score');
        const player2Score = document.querySelector('.player2-score');
        
        // Actualizar nombres finales
        document.getElementById('finalPlayer1Name').textContent = data.player1;
        document.getElementById('finalPlayer2Name').textContent = data.player2;
        
        // Actualizar puntuaciones
        player1Score.textContent = data.final_score.left;
        player2Score.textContent = data.final_score.right;
        
        // Configurar estilo según victoria/derrota
        if (data.winner === playerSide) {
            gameOverScreen.classList.add('victory');
            gameOverScreen.classList.remove('defeat');
            winnerText.textContent = '¡Victoria!';
            resultIcon.className = 'fas fa-trophy';
        } else {
            gameOverScreen.classList.add('defeat');
            gameOverScreen.classList.remove('victory');
            winnerText.textContent = 'Derrota';
            resultIcon.className = 'fas fa-flag'; // Cambiamos el icono a uno más elegante
        }
        
        // Configurar el botón de retorno
        const returnButton = document.getElementById('returnToLobby');
        returnButton.onclick = () => {
            window.location.href = '/game';
        };
        
        gameOverScreen.style.display = 'flex';
        
        // Animaciones de números
        animateScore(player1Score, data.final_score.left);
        animateScore(player2Score, data.final_score.right);
    }

    function animateScore(element, finalScore) {
        let start = 0;
        const duration = 1000;
        const startTime = performance.now();
        
        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const current = Math.floor(progress * finalScore);
            element.textContent = current;
            
            if (progress < 1) {
                requestAnimationFrame(update);
            }
        }
        
        requestAnimationFrame(update);
    }

    function handleKeyDown(e) {
        e.preventDefault();
        if (!playerSide) return;

        const key = e.key.toLowerCase();
        const isValidKey = (playerSide === 'left' && (key === 'w' || key === 's')) ||
                          (playerSide === 'right' && (key === 'arrowup' || key === 'arrowdown'));
        
        if (!isValidKey) return;

        activeKeys.add(key);
        // No enviamos mensaje aquí, el intervalo se encarga
    }

    function handleKeyUp(e) {
        const key = e.key.toLowerCase();
        activeKeys.delete(key);

        // Si no hay teclas activas, enviar dirección 0
        if (activeKeys.size === 0) {
            const message = {
                type: 'move_paddle',
                direction: 0,
                side: playerSide,
                player_id: parseInt(userId)
            };
            socket.send(JSON.stringify(message));
        }
    }

    function getDirection() {
        if (playerSide === 'left') {
            if (activeKeys.has('w')) return -1;
            if (activeKeys.has('s')) return 1;
        } else {
            if (activeKeys.has('arrowup')) return -1;
            if (activeKeys.has('arrowdown')) return 1;
        }
        return 0;
    }

    function setupControls() {
        console.log('Configurando controles para lado:', playerSide);
        // Iniciar el intervalo de movimiento continuo
        movementInterval = setInterval(() => {
            if (activeKeys.size > 0) {
                const direction = getDirection();
                const message = {
                    type: 'move_paddle',
                    direction: direction,
                    side: playerSide,
                    player_id: parseInt(userId)
                };
                socket.send(JSON.stringify(message));
            }
        }, 16);  // ~60 FPS

        document.addEventListener('keydown', handleKeyDown);
        document.addEventListener('keyup', handleKeyUp);
    }

    // Añadir después de la configuración inicial
    const gameWrapper = document.querySelector('.game-wrapper');
    const fullscreenBtn = document.getElementById('fullscreenBtn');

    fullscreenBtn.addEventListener('click', () => {
        if (!document.fullscreenElement) {
            if (gameWrapper.requestFullscreen) {
                gameWrapper.requestFullscreen();
            } else if (gameWrapper.webkitRequestFullscreen) {
                gameWrapper.webkitRequestFullscreen();
            } else if (gameWrapper.msRequestFullscreen) {
                gameWrapper.msRequestFullscreen();
            }
            gameWrapper.classList.add('fullscreen');
            fullscreenBtn.innerHTML = '<i class="fas fa-compress"></i>';
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            } else if (document.msExitFullscreen) {
                document.msExitFullscreen();
            }
            gameWrapper.classList.remove('fullscreen');
            fullscreenBtn.innerHTML = '<i class="fas fa-expand"></i>';
        }
    });

    // Manejar cambios de pantalla completa
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
    document.addEventListener('mozfullscreenchange', handleFullscreenChange);
    document.addEventListener('MSFullscreenChange', handleFullscreenChange);

    function handleFullscreenChange() {
        if (!document.fullscreenElement && !document.webkitFullscreenElement &&
            !document.mozFullScreenElement && !document.msFullscreenElement) {
            gameWrapper.classList.remove('fullscreen');
            fullscreenBtn.innerHTML = '<i class="fas fa-expand"></i>';
        }
    }

    // Cleanup mejorado
    return () => {
        if (movementInterval) {
            clearInterval(movementInterval);
            movementInterval = null;
        }
        document.removeEventListener('keydown', handleKeyDown);
        document.removeEventListener('keyup', handleKeyUp);
        socket.close();
        
        // Eliminar el CSS si no hay otras vistas que lo usen
        const cssLink = document.querySelector('link[href="/css/game.css"]');
        if (cssLink) {
            document.head.removeChild(cssLink);
        }

        document.removeEventListener('fullscreenchange', handleFullscreenChange);
        document.removeEventListener('webkitfullscreenchange', handleFullscreenChange);
        document.removeEventListener('mozfullscreenchange', handleFullscreenChange);
        document.removeEventListener('MSFullscreenChange', handleFullscreenChange);
    };
}
