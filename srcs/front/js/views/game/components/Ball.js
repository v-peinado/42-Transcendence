export class Ball {
    constructor(x = 0, y = 0, radius = 10) {
        this.pos = { x, y };
        this.vel = { x: 0, y: 0 };
        this.radius = radius;
        this.trailPoints = [];
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

    draw(ctx, theme) {
        // Dibujar trail si está activo
        if (theme.trail) {
            this.drawTrail(ctx, theme);
        }

        // Aplicar glow si existe
        if (theme.glow) {
            ctx.shadowBlur = 15;
            ctx.shadowColor = theme.glow;
        }

        ctx.fillStyle = theme.color;
        ctx.beginPath();
        ctx.arc(this.pos.x, this.pos.y, theme.size, 0, Math.PI * 2);
        ctx.fill();

        // Restaurar contexto
        ctx.shadowBlur = 0;

        // Actualizar trail
        if (theme.trail) {
            this.trailPoints.unshift({x: this.pos.x, y: this.pos.y});
            if (this.trailPoints.length > 5) {
                this.trailPoints.pop();
            }
        }
    }

    drawTrail(ctx, theme) {
        this.trailPoints.forEach((point, index) => {
            const alpha = (1 - index / this.trailPoints.length) * 0.3;
            ctx.fillStyle = `${theme.color}${Math.floor(alpha * 255).toString(16).padStart(2, '0')}`;
            ctx.beginPath();
            ctx.arc(point.x, point.y, theme.size * (1 - index / this.trailPoints.length), 0, Math.PI * 2);
            ctx.fill();
        });
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