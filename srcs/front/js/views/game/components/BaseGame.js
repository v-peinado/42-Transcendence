import { Ball } from './Ball.js';
import { Paddle } from './Paddle.js';

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
            BALL_SPEED: 7,  // Esta velocidad base está sobreescribiendo la velocidad de la dificultad
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

        this.initializeGame();
        this.setupEventListeners();
        this.loop = this.loop.bind(this);
    }

    initializeGame() {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;

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
        this.ctx.fillStyle = 'rgba(16, 19, 34, 0.95)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // Línea central
        this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
        this.ctx.setLineDash([10, 10]);
        this.ctx.beginPath();
        this.ctx.moveTo(this.canvas.width / 2, 0);
        this.ctx.lineTo(this.canvas.width / 2, this.canvas.height);
        this.ctx.stroke();
        this.ctx.setLineDash([]);

        this.ball.draw(this.ctx);
        this.leftPaddle.draw(this.ctx);
        this.rightPaddle.draw(this.ctx);
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
        this.ball.pos.y = Math.random() * this.canvas.height;
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
}
