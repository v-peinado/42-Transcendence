export class Paddle {
    constructor(x, y, width = 10, height = 160, isLeft = true) {
        this.pos = { x, y };
        this.width = width;
        this.height = height;
        this.isLeft = isLeft;
        this.score = 0;
        this.speed = 7;
    }

    draw(ctx) {
        ctx.fillStyle = 'white';
        ctx.fillRect(this.pos.x, this.pos.y, this.width, this.height);
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