export async function GameMatchView(gameId) {
    console.log('Iniciando partida:', gameId);
    const app = document.getElementById('app');
    
    app.innerHTML = `
        <div class="game-container">
            <canvas id="gameCanvas"></canvas>
            <div class="score" id="player1Score">0</div>
            <div class="score" id="player2Score">0</div>
            <div class="game-info">
                <div class="game-id">Partida ID: ${gameId}</div>
                <div id="gameStatus">Conectando...</div>
                <div id="playerInfo">Esperando asignación...</div>
                <div id="controlsInfo"></div>
            </div>
            <div id="countdown" class="countdown" style="display: none;"></div>
            <div id="gameOverScreen" class="game-over-screen" style="display: none;">
                <div class="game-over-content">
                    <h2 id="winnerText"></h2>
                    <div id="finalScore"></div>
                    <button id="returnToLobby" class="btn btn-primary">Volver al Lobby</button>
                </div>
            </div>
        </div>
    `;

    // estilos temporales, tengo que moverlos al css
    const style = document.createElement('style');
    style.textContent = `
        .game-container {
            position: relative;
            width: 1000px;
            height: 600px;
            margin: 0 auto;
        }
        #gameCanvas {
            background: rgb(85, 5, 45);
            border: 1px solid #000;
        }
        .score {
            position: absolute;
            color: rgb(28, 42, 236);
            font-size: 3rem;
            font-family: 'roboto';
            top: 50%;
            transform: translateY(-50%);
        }
        #player1Score { left: 35%; }
        #player2Score { right: 35%; }
        .game-info {
            position: absolute;
            width: 100%;
            text-align: center;
            color: rgb(28, 42, 236);
            padding: 10px;
            top: 10px;
            font-family: 'roboto';
        }
        #gameStatus, #playerInfo, #controlsInfo {
            margin: 5px 0;
            font-weight: bold;
        }
        .countdown {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 64px;
            color: white;
        }
        .game-over-screen {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 100;
        }
        .game-over-content {
            background: rgb(85, 5, 45);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            color: white;
        }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            background: #007bff;
            color: white;
        }
    `;
    document.head.appendChild(style);

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
        document.getElementById('gameStatus').textContent = 'Conectado - Esperando inicio...';
    };

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        // Solo logear mensajes que no sean del estado del juego
        if (data.type !== 'game_state') {
            console.log('Mensaje recibido:', data);
        }

        switch(data.type) {
            case 'game_start':
                console.log('Game Start Data:', {
                    player1_id: data.player1_id,
                    player2_id: data.player2_id,
                    myId: userId,
                    player1: data.player1,
                    player2: data.player2
                });

                // Asignar lado y actualizar UI
                if (userId && data.player1_id && data.player2_id) {
                    if (userId === data.player1_id.toString()) {
                        playerSide = 'left';
                        document.getElementById('playerInfo').textContent = 
                            `Tú eres el Jugador 1 - ${data.player1} (Izquierda)`;
                        document.getElementById('controlsInfo').textContent = 
                            'Controles: W/S para arriba/abajo';
                    } else if (userId === data.player2_id.toString()) {
                        playerSide = 'right';
                        document.getElementById('playerInfo').textContent = 
                            `Tú eres el Jugador 2 - ${data.player2} (Derecha)`;
                        document.getElementById('controlsInfo').textContent = 
                            'Controles: ↑/↓ para arriba/abajo';
                    }
                    
                    console.log('Lado asignado:', playerSide);
                    document.getElementById('gameStatus').textContent = '¡Partida iniciada!';
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

        ctx.fillStyle = 'rgb(85, 5, 45)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Dibujar raquetas
        ctx.fillStyle = 'white';
        Object.values(gameState.paddles).forEach(paddle => {
            ctx.fillRect(paddle.x, paddle.y, paddle.width, paddle.height);
        });

        // Dibujar pelota
        ctx.beginPath();
        ctx.arc(gameState.ball.x, gameState.ball.y, gameState.ball.radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.closePath();
    }

    function handleGameEnd(data) {
        const isWinner = data.winner === playerSide;
        const gameOverScreen = document.getElementById('gameOverScreen');
        const winnerText = document.getElementById('winnerText');
        const finalScore = document.getElementById('finalScore');
        
        winnerText.textContent = isWinner ? '¡Has ganado!' : 'Has perdido';
        finalScore.textContent = `Puntuación final: ${data.final_score.left} - ${data.final_score.right}`;
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

    // Cleanup mejorado
    return () => {
        if (movementInterval) {
            clearInterval(movementInterval);
            movementInterval = null;
        }
        document.removeEventListener('keydown', handleKeyDown);
        document.removeEventListener('keyup', handleKeyUp);
        socket.close();
        document.head.removeChild(style);
    };
}
