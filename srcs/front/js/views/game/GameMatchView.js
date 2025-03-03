import { loadHTML } from '../../utils/htmlLoader.js';
import { soundService } from '../../services/SoundService.js';
import AuthService from '../../services/AuthService.js';
import { getNavbarHTML } from '../../components/Navbar.js'; // Añadir esta importación

export async function GameMatchView(gameId) {
    console.log('Iniciando partida:', gameId);
    const app = document.getElementById('app');
    
    // Cargar navbar autenticado y template del juego
    const [template, userInfo] = await Promise.all([
        loadHTML('/views/game/templates/GameMatch.html'),
        AuthService.getUserProfile()
    ]);

    // Obtener el navbar procesado y añadirlo
    const navbarHtml = await getNavbarHTML(true, userInfo);
    
    // Preparar el contenido
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = template;
    
    // Limpiar y añadir el nuevo contenido con navbar
    app.innerHTML = navbarHtml;
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
        console.log('Mensaje recibido en GameMatchView:', data); // Debug

        switch(data.type) {
            case 'game_start':
                console.log('Iniciando juego:', data);
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
                break;

            case 'game_state':
                if (!gameState) {
                    console.log('Inicializando estado del juego');
                    gameState = data.state;
                }
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
        if (!state) return;
        
        gameState = state;
        
        // Actualizar marcador si existe
        const leftScore = document.querySelector('.minimal-header .player-score:first-child');
        const rightScore = document.querySelector('.minimal-header .player-score:last-child');
        if (leftScore && rightScore) {
            leftScore.textContent = state.paddles.left.score || '0';
            rightScore.textContent = state.paddles.right.score || '0';
        }

        // Dibujar el estado del juego
        drawGame();
    }

    function drawGame() {
        if (!gameState || !ctx) return;

        // Limpiar canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Fondo
        ctx.fillStyle = 'rgba(16, 19, 34, 0.95)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Línea central
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
        ctx.setLineDash([10, 10]);
        ctx.beginPath();
        ctx.moveTo(canvas.width / 2, 0);
        ctx.lineTo(canvas.width / 2, canvas.height);
        ctx.stroke();
        ctx.setLineDash([]);

        // Dibujar palas
        ctx.fillStyle = 'white';
        Object.values(gameState.paddles).forEach(paddle => {
            ctx.fillRect(paddle.x, paddle.y, paddle.width, paddle.height);
        });

        // Dibujar pelota
        if (gameState.ball) {
            ctx.beginPath();
            ctx.arc(gameState.ball.x, gameState.ball.y, gameState.ball.radius || 5, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    function handleGameEnd(data) {
        const gameOverScreen = document.getElementById('gameOverScreen');
        const winnerText = document.getElementById('winnerText');
        const resultIcon = document.querySelector('.result-icon i');
        const player1Score = document.querySelector('.player1-score');
        const player2Score = document.querySelector('.player2-score');
        
        // Determinar jugadores según el lado
        const leftPlayerName = document.querySelector('#leftPlayerName').textContent;
        const rightPlayerName = document.querySelector('#rightPlayerName').textContent;
        
        // Actualizar nombres finales con los nombres correctos
        document.getElementById('finalPlayer1Name').textContent = leftPlayerName;
        document.getElementById('finalPlayer2Name').textContent = rightPlayerName;
        
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
            resultIcon.className = 'fas fa-flag';
        }
        
        // Simplificar la configuración del botón de retorno
        document.getElementById('returnToLobby').onclick = () => {
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
