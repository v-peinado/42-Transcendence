export class Ball {
    constructor(x = 0, y = 0, radius = 10) {
        this.pos = { x, y };
        this.vel = { x: 0, y: 0 };
        this.radius = radius;
    }

    setSpeed(speedX, speedY) {
        // Asegurarnos que la velocidad es exactamente la especificada
        this.vel.x = speedX;
        this.vel.y = speedY;
    }

    setPosition(x, y) {
        this.pos.x = x;
        this.pos.y = y;
    }

    draw(ctx) {
        ctx.beginPath();
        ctx.arc(this.pos.x, this.pos.y, this.radius, 0, Math.PI * 2);
        ctx.fillStyle = 'white';
        ctx.fill();
        ctx.closePath();
    }

    update() {
        this.pos.x += this.vel.x;
        this.pos.y += this.vel.y;
    }

    collisionWithEdges(canvas) {
        if (this.pos.y + this.radius > canvas.height || this.pos.y - this.radius < 0) {
            this.vel.y *= -1;
        }
    }

    collisionWithPaddle(paddle) {
        const ballLeft = this.pos.x - this.radius;
        const ballRight = this.pos.x + this.radius;
        const ballTop = this.pos.y - this.radius;
        const ballBottom = this.pos.y + this.radius;

        const paddleLeft = paddle.pos.x;
        const paddleRight = paddle.pos.x + paddle.width;
        const paddleTop = paddle.pos.y;
        const paddleBottom = paddle.pos.y + paddle.height;

        if (ballRight >= paddleLeft && 
            ballLeft <= paddleRight && 
            ballBottom >= paddleTop && 
            ballTop <= paddleBottom) {
            
            // Calcular punto de impacto relativo
            const relativeIntersectY = (paddle.pos.y + (paddle.height/2)) - this.pos.y;
            const normalizedIntersectY = relativeIntersectY / (paddle.height/2);
            const bounceAngle = normalizedIntersectY * Math.PI/3;

            const speed = Math.sqrt(this.vel.x * this.vel.x + this.vel.y * this.vel.y);
            
            this.vel.x = -this.vel.x;
            this.vel.y = -speed * Math.sin(bounceAngle);
        }
    }

    getState() {
        return {
            x: this.pos.x,
            y: this.pos.y,
            radius: this.radius,
            speed: { x: this.vel.x, y: this.vel.y }
        };
    }
}