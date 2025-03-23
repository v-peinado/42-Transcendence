export class Paddle {
    constructor(x, y, width = 10, height = 160, isLeft = true) {
        this.pos = { x, y };
        this.width = width;
        this.height = height;
        this.isLeft = isLeft;
        this.score = 0;
        this.speed = 7;
    }

    draw(ctx, theme) {
        if (theme.glow) {
            ctx.shadowBlur = 15;
            ctx.shadowColor = theme.glow;
        }

        ctx.fillStyle = theme.color;
        if (theme.pixelated) {
            this.drawPixelated(ctx, theme);
        } else {
            ctx.fillRect(this.pos.x, this.pos.y, theme.width, theme.height);
        }

        // Restaurar contexto
        ctx.shadowBlur = 0;
    }

    drawPixelated(ctx, theme) {
        const pixelSize = 4;
        for (let y = 0; y < theme.height; y += pixelSize) {
            for (let x = 0; x < theme.width; x += pixelSize) {
                ctx.fillRect(
                    this.pos.x + x,
                    this.pos.y + y,
                    pixelSize - 1,
                    pixelSize - 1
                );
            }
        }
    }

    move(direction) {
        this.pos.y += direction * this.speed;
    }

    setPosition(y) {
        this.pos.y = y;
    }

    setSpeed(speed) {
        this.speed = speed;
    }

    getState() {
        return {
            x: this.pos.x,
            y: this.pos.y,
            width: this.width,
            height: this.height,
            score: this.score
        };
    }

    constrainToCanvas(canvasHeight) {
        if (this.pos.y < 0) this.pos.y = 0;
        if (this.pos.y + this.height > canvasHeight) {
            this.pos.y = canvasHeight - this.height;
        }
    }
}