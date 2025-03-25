import { BaseGame } from './BaseGame.js';

export class SinglePlayerGame extends BaseGame {
    constructor(canvas, difficulty, maxPoints, onGameEnd) {
        super(canvas, maxPoints, onGameEnd);
        
        // Handler para prevenir scroll
        this.handleKeyDown = (e) => {
            if([38, 40].includes(e.keyCode)) {
                e.preventDefault();
            }
        };
        
        // Añadir event listener
        window.addEventListener('keydown', this.handleKeyDown);

        // Configuración de dificultad idéntica a Django
        const DIFFICULTY = {
            easy: {
                RANDOMNESS: 40,
                MISS_CHANCE: 0.3,
                AI_REACTION_DELAY: 300,
                BALL_SPEED: 5,
                PADDLE_SPEED: 7
            },
            medium: {
                RANDOMNESS: 25,
                MISS_CHANCE: 0.1,
                AI_REACTION_DELAY: 150,
                BALL_SPEED: 6,
                PADDLE_SPEED: 7
            },
            hard: {
                RANDOMNESS: 10,
                MISS_CHANCE: 0.05,
                AI_REACTION_DELAY: 80,
                BALL_SPEED: 7,
                PADDLE_SPEED: 7
            }
        };

        // Actualizar dificultad y velocidades
        this.updateDifficulty = (newDifficulty) => {
            this.difficulty = DIFFICULTY[newDifficulty] || DIFFICULTY.medium;
            
            // Actualizar velocidad de la bola
            const currentSpeedX = Math.abs(this.ball.vel.x);
            const currentSpeedY = Math.abs(this.ball.vel.y);
            const dirX = this.ball.vel.x >= 0 ? 1 : -1;
            const dirY = this.ball.vel.y >= 0 ? 1 : -1;
            
            this.ball.vel.x = dirX * this.difficulty.BALL_SPEED;
            this.ball.vel.y = dirY * this.difficulty.BALL_SPEED;
            
            // Actualizar velocidad de los paddles
            this.leftPaddle.speed = this.difficulty.PADDLE_SPEED;
            this.rightPaddle.speed = this.difficulty.PADDLE_SPEED;
        };

        // Aplicar configuración inicial
        this.updateDifficulty(difficulty);

        this.difficulty = DIFFICULTY[difficulty] || DIFFICULTY.medium;
        this.lastAIUpdate = 0;
        this.AI_INTERVAL = 1000; // Cambiar a 1000 como en Django
        this.rightPaddle.targetY = canvas.height / 2;
        
        // Actualizar velocidad de la bola según dificultad
        this.ball.setSpeed(this.difficulty.BALL_SPEED, this.difficulty.BALL_SPEED);
        this.rightPaddle.vel = { x: 0, y: this.difficulty.BALL_SPEED }; // Añadir vel como en Django

        // Asegurarnos que la velocidad se actualiza cuando cambia la dificultad
        this.updateBallSpeed = () => {
            const speed = this.difficulty.BALL_SPEED;
            const dirX = this.ball.vel.x >= 0 ? 1 : -1;
            const dirY = this.ball.vel.y >= 0 ? 1 : -1;
            this.ball.vel.x = dirX * speed;
            this.ball.vel.y = dirY * speed;
        };

        // Aplicar la velocidad inicial
        this.updateBallSpeed();
    }

    predictBallY() {
        if (this.ball.vel.x <= 0) {
            return this.ball.pos.y;
        }

        let tempBall = {
            pos: { x: this.ball.pos.x, y: this.ball.pos.y },
            vel: { x: this.ball.vel.x, y: this.ball.vel.y },
            rad: this.ball.radius
        };

        let maxIterations = 500;
        let iterations = 0;

        // Lógica idéntica a Django
        while (tempBall.pos.x < this.rightPaddle.pos.x && iterations < maxIterations) {
            tempBall.pos.x += tempBall.vel.x;
            tempBall.pos.y += tempBall.vel.y;
            iterations++;

            // Colisiones mejoradas como en Django
            if (tempBall.pos.y + tempBall.rad >= this.canvas.height) {
                tempBall.pos.y = this.canvas.height - tempBall.rad;
                tempBall.vel.y *= -1;
            } else if (tempBall.pos.y - tempBall.rad <= 0) {
                tempBall.pos.y = tempBall.rad;
                tempBall.vel.y *= -1;
            }
        }

        if (iterations === maxIterations) {
            console.warn("predictBallY reached maximum iterations.");
        }

        const errorMargin = 15;
        const randomError = (Math.random() * 2 * errorMargin) - errorMargin;
        let predictedY = tempBall.pos.y + randomError;
        return Math.max(this.ball.radius, Math.min(this.canvas.height - this.ball.radius, predictedY));
    }

    player2AI(timestamp) {
        if (timestamp - this.lastAIUpdate >= this.AI_INTERVAL) {
            this.lastAIUpdate = timestamp;

            // Exactamente la misma lógica que en Django
            let predictedY = this.predictBallY();
            const randomness = Math.random() * this.difficulty.RANDOMNESS - (this.difficulty.RANDOMNESS / 2);
            let targetY = predictedY + randomness;

            // Misma lógica de miss chance
            if (Math.random() < this.difficulty.MISS_CHANCE) {
                targetY = Math.random() * this.canvas.height;
            }
            this.rightPaddle.targetY = targetY;

            // Mismo sistema de movimiento
            const paddleCenter = this.rightPaddle.pos.y + this.rightPaddle.height / 2;
            if (paddleCenter < this.rightPaddle.targetY - 5) {
                this.rightPaddle.pos.y += this.rightPaddle.speed;
            } else if (paddleCenter > this.rightPaddle.targetY + 5) {
                this.rightPaddle.pos.y -= this.rightPaddle.speed;
            }

            // Misma restricción de movimiento
            this.rightPaddle.pos.y = Math.max(0, Math.min(this.canvas.height - this.rightPaddle.height, this.rightPaddle.pos.y));
            
            // Mismo delay de reacción
            setTimeout(() => {
                this.simulateKeyUp(this.KEY_UP);
                this.simulateKeyUp(this.KEY_DOWN);
            }, this.difficulty.AI_REACTION_DELAY + Math.random() * 200);
        }
    }

    paddleUpdate(paddle) {
        const paddleCenter = paddle.pos.y + paddle.height / 2;
        const speed = paddle.speed;

        // Ajuste para que coincida exactamente con la lógica de Django
        if (paddleCenter < paddle.targetY - 5) {
            paddle.pos.y += speed;
        } else if (paddleCenter > paddle.targetY + 5) {
            paddle.pos.y -= speed;
        }

        // Restricción de movimiento idéntica a Django
        paddle.pos.y = Math.max(0, Math.min(this.canvas.height - paddle.height, paddle.pos.y));
    }

    // Añadir métodos de simulación de teclas como en Django
    simulateKeyDown(keyCode) {
        const event = new KeyboardEvent('keydown', { keyCode });
        window.dispatchEvent(event);
    }

    simulateKeyUp(keyCode) {
        const event = new KeyboardEvent('keyup', { keyCode });
        window.dispatchEvent(event);
    }

    update(timestamp) {
        if (!this.ball || !this.leftPaddle || !this.rightPaddle) return;

        this.ball.update();
        
        // Control del jugador
        if (this.keys[this.KEY_W]) this.leftPaddle.move(-1);
        if (this.keys[this.KEY_S]) this.leftPaddle.move(1);
        
        // Actualización de la IA como en Django
        this.player2AI(timestamp);
        this.paddleUpdate(this.rightPaddle);
        
        this.handleCollisions();
        this.checkScore();
        this.updateGameState();
    }

    destroy() {
        // Eliminar event listener al destruir el juego
        window.removeEventListener('keydown', this.handleKeyDown);
        super.destroy(); // Si existe un método destroy en la clase padre
    }

    respawnBall() {
        super.respawnBall();
        // Mantener la velocidad correcta después del respawn
        const dirX = this.ball.vel.x >= 0 ? 1 : -1;
        const dirY = this.ball.vel.y >= 0 ? 1 : -1;
        this.ball.vel.x = dirX * this.difficulty.BALL_SPEED;
        this.ball.vel.y = dirY * this.difficulty.BALL_SPEED;
    }
}
