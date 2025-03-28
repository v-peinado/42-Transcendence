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
        if (this.pos.y + this.radius >= canvas.height) {
            // Corrige la posición para que no atraviese el borde inferior
            this.pos.y = canvas.height - this.radius;
            this.vel.y *= -1;
        } else if (this.pos.y - this.radius <= 0) {
            // Corrige la posición para que no atraviese el borde superior
            this.pos.y = this.radius;
            this.vel.y *= -1;
        }
    }
    
    collisionWithPaddle(paddle) {
        // Calcular la distancia entre el centro de la pelota y el centro de la pala
        let dx = Math.abs(this.pos.x - paddle.pos.x - paddle.width / 2);
        let dy = Math.abs(this.pos.y - paddle.pos.y - paddle.height / 2);
        
        // Si se detecta colisión
        if (dx <= (this.radius + paddle.width / 2) && dy <= (this.radius + paddle.height / 2)) {
            if (dx > paddle.width / 2) {
                // Colisión en los laterales: usar la lógica de ángulo de rebote
                let relativeIntersectY = this.pos.y - (paddle.pos.y + paddle.height / 2);
                let normalizedIntersect = relativeIntersectY / (paddle.height / 2);
                let bounceAngle = normalizedIntersect * (Math.PI / 4);  // máximo 45 grados
                
                // Añadir variación aleatoria al ángulo de rebote (±0.05 radianes)
                bounceAngle += (Math.random() * 0.1 - 0.05);
                
                // Usar la velocidad actual para mantener la magnitud
                let speed = Math.sqrt(this.vel.x * this.vel.x + this.vel.y * this.vel.y);
                
                if (this.vel.x < 0) {
                    this.vel.x = speed * Math.cos(bounceAngle);
                    this.vel.y = speed * Math.sin(bounceAngle);
                    this.pos.x = paddle.pos.x + paddle.width + this.radius;
                } else {
                    this.vel.x = -speed * Math.cos(bounceAngle);
                    this.vel.y = speed * Math.sin(bounceAngle);
                    this.pos.x = paddle.pos.x - this.radius;
                }
            } else if (dy > paddle.height / 2) {
                // Colisión en la parte superior o inferior: invertir velocidad vertical
                this.vel.y *= -1;
                if (this.pos.y < paddle.pos.y) {
                    this.pos.y = paddle.pos.y - this.radius;
                } else {
                    this.pos.y = paddle.pos.y + paddle.height + this.radius;
                }
            } else {
                // Colisión en la esquina: invertir ambas velocidades
                this.vel.x *= -1;
                this.vel.y *= -1;
                if (this.pos.x < paddle.pos.x) {
                    this.pos.x = paddle.pos.x - this.radius;
                } else if (this.pos.x > paddle.pos.x + paddle.width) {
                    this.pos.x = paddle.pos.x + paddle.width + this.radius;
                }
                if (this.pos.y < paddle.pos.y) {
                    this.pos.y = paddle.pos.y - this.radius;
                } else if (this.pos.y > paddle.pos.y + paddle.height) {
                    this.pos.y = paddle.pos.y + paddle.height + this.radius;
                }
            }
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