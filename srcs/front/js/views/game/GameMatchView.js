import { loadHTML } from '../../utils/htmlLoader.js';

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

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type !== 'game_state') {
            console.log('Mensaje recibido:', data);
        }

        switch(data.type) {
            case 'game_start':
                console.log('Game Start Data:', data);

                // Asignar lado y actualizar UI de forma segura
                if (userId && data.player1_id && data.player2_id) {
                    const player1Name = document.getElementById('player1Name');
                    const player2Name = document.getElementById('player2Name');
                    const leftControls = document.getElementById('leftControls');
                    const rightControls = document.getElementById('rightControls');
                    const gameStatus = document.getElementById('gameStatus');

                    // Actualizar nombres de ambos jugadores
                    if (player1Name) player1Name.textContent = data.player1;
                    if (player2Name) player2Name.textContent = data.player2;

                    if (userId === data.player1_id.toString()) {
                        playerSide = 'left';
                        if (leftControls) leftControls.style.display = 'block';
                        if (rightControls) rightControls.style.display = 'none';
                    } else if (userId === data.player2_id.toString()) {
                        playerSide = 'right';
                        if (rightControls) rightControls.style.display = 'block';
                        if (leftControls) leftControls.style.display = 'none';
                    }

                    if (gameStatus) {
                        gameStatus.textContent = '🔥 ¡Partida en curso!';
                    }

                    setupControls();
                } else {
                    console.error('Datos de jugador incompletos:', {
                        userId, 
                        player1Id: data.player1_id, 
                        player2Id: data.player2_id
                    });
                }
                break;
            case 'game_state':
                handleGameState(data.state);
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
        gameState = state;
        requestAnimationFrame(drawGame);

        // Actualizar marcador
        document.getElementById('player1Score').textContent = state.paddles.left.score;
        document.getElementById('player2Score').textContent = state.paddles.right.score;

        // Mostrar cuenta regresiva si existe
        if (state.countdown !== undefined) {
            const countdown = document.getElementById('countdown');
            countdown.style.display = 'block';
            countdown.textContent = state.countdown;
        }
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
        const isWinner = data.winner === playerSide;
        const gameOverScreen = document.getElementById('gameOverScreen');
        const winnerText = document.getElementById('winnerText');
        const finalScore = document.getElementById('finalScore');
        
        if (isWinner) {
            winnerText.textContent = '🏆 ¡Victoria!';
            winnerText.className = 'winner-text victory';
        } else {
            winnerText.textContent = '💔 Derrota';
            winnerText.className = 'winner-text defeat';
        }
        
        finalScore.innerHTML = `
            <div class="score-detail">
                <span class="score-label">Puntuación Final:</span>
                <span class="score-numbers">${data.final_score.left} - ${data.final_score.right}</span>
            </div>
        `;
        
        gameOverScreen.style.display = 'flex';

        // Detener controles
        if (movementInterval) {
            clearInterval(movementInterval);
            movementInterval = null;
        }
        document.removeEventListener('keydown', handleKeyDown);
        document.removeEventListener('keyup', handleKeyUp);

        // Añadir evento al botón de retorno
        document.getElementById('returnToLobby').onclick = () => {
            window.location.href = '/game';
        };
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
