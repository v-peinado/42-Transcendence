import { Ball } from './Ball.js';
import { Paddle } from './Paddle.js';
import { GameThemes, defaultTheme } from './GameThemes.js';

export class BaseGame {
    constructor(canvas, maxPoints, onGameEnd) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.canvas.width = 1000;
        this.canvas.height = 600;
        
        this.maxPoints = maxPoints;
        this.onGameEnd = onGameEnd;
        
        // Configuración básica común
        this.difficulty = {
            PADDLE_HEIGHT: 100,
            BALL_SPEED: 6.4,  // Esta velocidad base está sobreescribiendo la velocidad de la dificultad
            PADDLE_SPEED: 7
        };

        // Score tracking y estado del juego
        this.player1Points = 0;
        this.player2Points = 0;
        this.gameEnded = false;
        this.keys = {};

        // Teclas comunes
        this.KEY_W = 87;
        this.KEY_S = 83;
        this.KEY_UP = 38;
        this.KEY_DOWN = 40;

        // Añadir soporte para temas
        this.currentTheme = localStorage.getItem('pongTheme') ? 
            JSON.parse(localStorage.getItem('pongTheme')) : 
            defaultTheme;

        this.isPaused = false;
        
        // Cambiar ESC por ESPACIO
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space') {
                e.preventDefault(); // Prevenir scroll
                this.togglePause();
            }
        });

        this.initializeGame();
        this.setupEventListeners();
        this.loop = this.loop.bind(this);
    }

    initializeGame() {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;

        // Añadir botón de pausa
        const pauseButton = document.createElement('button');
        pauseButton.className = 'pause-button';
        pauseButton.innerHTML = '<i class="fas fa-pause"></i>';
        pauseButton.onclick = () => this.togglePause();
        this.canvas.parentElement.appendChild(pauseButton);

        this.ball = new Ball(centerX, centerY, 10);
        this.ball.setSpeed(this.difficulty.BALL_SPEED, this.difficulty.BALL_SPEED);

        this.leftPaddle = new Paddle(10, centerY - this.difficulty.PADDLE_HEIGHT/2, 10, this.difficulty.PADDLE_HEIGHT, true);
        this.rightPaddle = new Paddle(this.canvas.width - 20, centerY - this.difficulty.PADDLE_HEIGHT/2, 10, this.difficulty.PADDLE_HEIGHT, false);

        this.gameState = {
            status: 'playing',
            countdown: null,
            play_sound: false,
            paddles: {
                left: this.leftPaddle.getState(),
                right: this.rightPaddle.getState()
            },
            ball: this.ball.getState()
        };
    }

    handleCollisions() {
        this.ball.collisionWithEdges(this.canvas);
        this.ball.collisionWithPaddle(this.leftPaddle);
        this.ball.collisionWithPaddle(this.rightPaddle);
        
        this.leftPaddle.constrainToCanvas(this.canvas.height);
        this.rightPaddle.constrainToCanvas(this.canvas.height);
    }

    // Métodos comunes
    setupEventListeners() {
        document.addEventListener('keydown', (e) => {
            this.keys[e.keyCode] = true;
        });

        document.addEventListener('keyup', (e) => {
            this.keys[e.keyCode] = false;
        });
    }

    draw() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Aplicar tema al campo
        this.ctx.fillStyle = this.currentTheme.field.background;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // Línea central con tema
        this.ctx.strokeStyle = this.currentTheme.field.lineColor;
        this.ctx.setLineDash(this.currentTheme.field.lineDash);
        this.ctx.beginPath();
        this.ctx.moveTo(this.canvas.width / 2, 0);
        this.ctx.lineTo(this.canvas.width / 2, this.canvas.height);
        this.ctx.stroke();
        this.ctx.setLineDash([]);

        // Dibujar elementos con tema
        this.ball.draw(this.ctx, this.currentTheme.ball);
        this.leftPaddle.draw(this.ctx, this.currentTheme.paddles);
        this.rightPaddle.draw(this.ctx, this.currentTheme.paddles);

        // Efectos especiales si están activados
        if (this.currentTheme.field.glow) {
            this.applyFieldGlow();
        }
    }

    applyFieldGlow() {
        this.ctx.shadowBlur = 20;
        this.ctx.shadowColor = this.currentTheme.field.lineColor;
        // Restaurar después de dibujar
        this.ctx.shadowBlur = 0;
    }

    loop(timestamp) {
        if (!this.gameEnded) {
            this.update(timestamp);
            this.draw();
            this.animationFrameId = requestAnimationFrame(this.loop);
        }
    }

    checkScore() {
        if (this.ball.pos.x <= 0) {
            this.player2Points++;
            this.updateScores();
            this.respawnBall();
        } else if (this.ball.pos.x >= this.canvas.width) {
            this.player1Points++;
            this.updateScores();
            this.respawnBall();
        }

        if (this.player1Points >= this.maxPoints || this.player2Points >= this.maxPoints) {
            const winner = this.player1Points > this.player2Points ? 'Player1' : 'Player2';
            if (this.onGameEnd) {
                this.onGameEnd(this.player1Points, this.player2Points, winner);
            }
            this.stop();
        }
    }

    updateScores() {
        const player1ScoreEl = document.getElementById('player1Score');
        const player2ScoreEl = document.getElementById('player2Score');

        if (player1ScoreEl) player1ScoreEl.textContent = this.player1Points;
        if (player2ScoreEl) player2ScoreEl.textContent = this.player2Points;
    }

    respawnBall() {
        this.ball.pos.x = this.canvas.width / 2;
        this.ball.pos.y = this.canvas.height / 2;
        this.ball.vel.x *= -1;
        if (Math.random() > 0.5) {
            this.ball.vel.y *= -1;
        }
    }

    getState() {
        return {
            status: 'playing',
            countdown: null,
            play_sound: false,
            paddles: {
                left: this.leftPaddle.getState(),
                right: this.rightPaddle.getState()
            },
            ball: this.ball.getState()
        };
    }

    updateGameState() {
        this.gameState = this.getState();
    }

    start() {
        if (!this.gameEnded) {
            this.animationFrameId = requestAnimationFrame(this.loop);
        }
        return this;
    }

    stop() {
        this.gameEnded = true;
        cancelAnimationFrame(this.animationFrameId);
        return this;
    }

    destroy() {
        this.gameEnded = true;
        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
        }
        
        // Eliminar el botón de pausa
        const pauseButton = document.querySelector('.pause-button');
        if (pauseButton) {
            pauseButton.remove();
        }
        
        // Eliminar event listeners
        document.removeEventListener('keydown', this.handleKeyDown);
        document.removeEventListener('keyup', this.handleKeyUp);
        
        // Limpiar canvas
        if (this.canvas && this.ctx) {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        }
        
        // Limpiar referencias
        this.ball = null;
        this.leftPaddle = null;
        this.rightPaddle = null;
        this.keys = {};
    }

    setTheme(themeName) {
        if (GameThemes[themeName]) {
            this.currentTheme = GameThemes[themeName];
            localStorage.setItem('pongTheme', JSON.stringify(this.currentTheme));
            return true;
        }
        return false;
    }

    togglePause() {
        this.isPaused = !this.isPaused;
        if (this.isPaused) {
            this.showPauseMenu();
            cancelAnimationFrame(this.animationFrameId);
        } else {
            this.hidePauseMenu();
            this.start();
        }
    }

    showPauseMenu() {
        const pauseMenu = document.createElement('div');
        pauseMenu.id = 'pauseMenu';
        pauseMenu.className = 'game-pause-modal';
        
        // Generar HTML para todos los temas disponibles
        const themeButtons = Object.entries(GameThemes).map(([key, theme]) => `
            <button data-theme="${key}" class="game-theme-btn ${this.currentTheme === theme ? 'active' : ''}">
                <i class="fas ${getThemeIcon(key)}"></i>
                <span>${theme.name}</span>
            </button>
        `).join('');

        pauseMenu.innerHTML = `
            <div class="game-pause-content">
                <div class="game-pause-header">
                    <h2 class="game-pause-title">
                        <i class="fas fa-pause-circle me-2"></i>
                        Juego Pausado
                    </h2>
                </div>
                <div class="game-theme-selector">
                    <h4 class="text-primary mb-3">
                        <i class="fas fa-paint-brush me-2"></i>
                        Personaliza tu juego
                    </h4>
                    <div class="game-theme-options">
                        ${themeButtons}
                    </div>
                </div>

                <div class="game-pause-actions">
                    <button class="game-pause-resume-btn">
                        <i class="fas fa-play me-2"></i>Reanudar
                    </button>
                    <button class="game-pause-quit-btn">
                        <i class="fas fa-sign-out-alt me-2"></i>Salir
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(pauseMenu);
        
        // Event listeners del menú
        pauseMenu.querySelector('.game-pause-resume-btn').onclick = () => this.togglePause();
        pauseMenu.querySelector('.game-pause-quit-btn').onclick = () => window.location.href = '/game';
        pauseMenu.querySelectorAll('.game-theme-btn').forEach(btn => {
            btn.onclick = () => {
                this.setTheme(btn.dataset.theme);
                pauseMenu.querySelectorAll('.game-theme-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            }
        });
    }

    hidePauseMenu() {
        const menu = document.getElementById('pauseMenu');
        if (menu) menu.remove();
    }
}

// Añadir función auxiliar para obtener el icono correspondiente a cada tema
function getThemeIcon(theme) {
    const icons = {
        classic: 'fa-circle',
        neon: 'fa-bolt',
        retro: 'fa-gamepad',
        cyberpunk: 'fa-microchip',
        matrix: 'fa-terminal',
        outrun: 'fa-car',       // Nuevo icono para Outrun
        cosmic: 'fa-stars'      // Nuevo icono para Cosmic
    };
    return icons[theme] || 'fa-circle';
}
