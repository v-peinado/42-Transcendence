import { BaseGame } from './BaseGame.js';
import { DIFFICULTY_LEVELS } from '../../../config/GameConfig.js';

export class SinglePlayerGame extends BaseGame {
    constructor(canvas, difficulty, maxPoints, onGameEnd) {
        super(canvas, maxPoints, onGameEnd);
        
        this.handleKeyDown = (e) => {
            if([38, 40].includes(e.keyCode)) {
                e.preventDefault();
            }
        };
        
        window.addEventListener('keydown', this.handleKeyDown);

        this.difficulty = DIFFICULTY_LEVELS[difficulty] || DIFFICULTY_LEVELS.medium;
        this.lastAIUpdate = 0;
        this.AI_INTERVAL = 1000;
        this.rightPaddle.targetY = canvas.height / 2;
        
        // Establecer velocidades iniciales
        this.updatePaddleSpeeds();
        this.updateBallSpeed();
    }

    updatePaddleSpeeds() {
        if (this.leftPaddle) this.leftPaddle.speed = this.difficulty.PADDLE_SPEED;
        if (this.rightPaddle) this.rightPaddle.speed = this.difficulty.PADDLE_SPEED;
    }

    updateBallSpeed() {
        if (!this.ball) return;
        
        const dirX = this.ball.vel.x >= 0 ? 1 : -1;
        const dirY = this.ball.vel.y >= 0 ? 1 : -1;
        this.ball.vel.x = dirX * this.difficulty.BALL_SPEED;
        this.ball.vel.y = dirY * this.difficulty.BALL_SPEED;
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

        while (tempBall.pos.x < this.rightPaddle.pos.x && iterations < maxIterations) {
            tempBall.pos.x += tempBall.vel.x;
            tempBall.pos.y += tempBall.vel.y;
            iterations++;

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

            let predictedY = this.predictBallY();
            const randomness = Math.random() * this.difficulty.RANDOMNESS - (this.difficulty.RANDOMNESS / 2);
            let targetY = predictedY + randomness;

            if (Math.random() < this.difficulty.MISS_CHANCE) {
                targetY = Math.random() * this.canvas.height;
            }
            this.rightPaddle.targetY = targetY;

            const paddleCenter = this.rightPaddle.pos.y + this.rightPaddle.height / 2;
            if (paddleCenter < this.rightPaddle.targetY - 5) {
                this.rightPaddle.pos.y += this.rightPaddle.speed;
            } else if (paddleCenter > this.rightPaddle.targetY + 5) {
                this.rightPaddle.pos.y -= this.rightPaddle.speed;
            }

            this.rightPaddle.pos.y = Math.max(0, Math.min(this.canvas.height - this.rightPaddle.height, this.rightPaddle.pos.y));
            
            setTimeout(() => {
                this.simulateKeyUp(this.KEY_UP);
                this.simulateKeyUp(this.KEY_DOWN);
            }, this.difficulty.AI_REACTION_DELAY + Math.random() * 200);
        }
    }

    paddleUpdate(paddle) {
        const paddleCenter = paddle.pos.y + paddle.height / 2;
        const speed = paddle.speed;

        if (paddleCenter < paddle.targetY - 5) {
            paddle.pos.y += speed;
        } else if (paddleCenter > paddle.targetY + 5) {
            paddle.pos.y -= speed;
        }

        paddle.pos.y = Math.max(0, Math.min(this.canvas.height - paddle.height, paddle.pos.y));
    }

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
        
        if (this.keys[this.KEY_W]) this.leftPaddle.move(-1);
        if (this.keys[this.KEY_S]) this.leftPaddle.move(1);
        
        this.player2AI(timestamp);
        this.paddleUpdate(this.rightPaddle);
        
        this.handleCollisions();
        this.checkScore();
        this.updateGameState();
    }

    destroy() {
        window.removeEventListener('keydown', this.handleKeyDown);
        super.destroy();
    }

    respawnBall() {
        super.respawnBall();
        const dirX = this.ball.vel.x >= 0 ? 1 : -1;
        const dirY = this.ball.vel.y >= 0 ? 1 : -1;
        this.ball.vel.x = dirX * this.difficulty.BALL_SPEED;
        this.ball.vel.y = dirY * this.difficulty.BALL_SPEED;
    }
}
