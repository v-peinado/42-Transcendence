import { DIFFICULTY_LEVELS } from '../../../config/GameConfig.js';

export class ThemePreview {
    constructor(canvasElement, theme) {
        this.canvas = canvasElement;
        this.ctx = this.canvas.getContext('2d');
        this.theme = theme;
        
        // Dimensiones más pequeñas para la previsualización
        this.width = 300;
        this.height = 180;
        
        // Configurar tamaño del canvas
        this.canvas.width = this.width;
        this.canvas.height = this.height;
        
        // Elementos del juego escalados
        this.paddleWidth = 6;
        this.paddleHeight = 50;
        this.ballSize = 6;
        
        // Posiciones iniciales
        this.paddle1Y = this.height/2 - this.paddleHeight/2;
        this.paddle2Y = this.height/2 - this.paddleHeight/2;
        this.ballX = this.width/2;
        this.ballY = this.height/2;
        
        // Añadir velocidad de la pelota para animación
        this.ballSpeedX = 2;
        this.ballSpeedY = 1.5;
        
        // Usar configuración "easy" para la demo
        this.config = DIFFICULTY_LEVELS.easy;
        
        this.animate();
    }
    
    animate() {
        // Actualizar posición de la pelota
        this.ballX += this.ballSpeedX;
        this.ballY += this.ballSpeedY;
        
        // Rebotar en los bordes
        if (this.ballX <= this.ballSize || this.ballX >= this.width - this.ballSize) {
            this.ballSpeedX *= -1;
        }
        if (this.ballY <= this.ballSize || this.ballY >= this.height - this.ballSize) {
            this.ballSpeedY *= -1;
        }

        // Limpiar canvas
        this.ctx.clearRect(0, 0, this.width, this.height);
        
        // Aplicar estilos del tema
        this.applyTheme();
        
        // Dibujar elementos
        this.drawField();
        this.drawPaddles();
        this.drawBall();
        
        // Continuar animación
        requestAnimationFrame(() => this.animate());
    }
    
    applyTheme() {
        // Aplicar fondo al contenedor en lugar del canvas
        const container = this.canvas.parentElement;
        if (this.theme.field?.background) {
            container.style.background = this.theme.field.background;
        }
        // Limpiar el canvas para el nuevo frame
        this.ctx.clearRect(0, 0, this.width, this.height);
    }
    
    drawField() {
        // Línea central
        this.ctx.beginPath();
        this.ctx.setLineDash([5, 5]);
        this.ctx.moveTo(this.width/2, 0);
        this.ctx.lineTo(this.width/2, this.height);
        this.ctx.strokeStyle = this.theme.field?.lineColor || 'rgba(255,255,255,0.2)';
        this.ctx.stroke();
        this.ctx.setLineDash([]); // Restaurar línea sólida
    }
    
    drawPaddles() {
        // Resetear sombras antes de dibujar
        this.ctx.shadowColor = 'transparent';
        this.ctx.shadowBlur = 0;
        
        // Aplicar efectos de brillo si están definidos
        if (this.theme.paddles?.glow) {
            this.ctx.shadowColor = this.theme.paddles.color;
            this.ctx.shadowBlur = 10;
        }
        
        this.ctx.fillStyle = this.theme.paddles?.color || 'white';
        
        // Paletas
        this.ctx.fillRect(10, this.paddle1Y, this.paddleWidth, this.paddleHeight);
        this.ctx.fillRect(this.width - 16, this.paddle2Y, this.paddleWidth, this.paddleHeight);
    }
    
    drawBall() {
        // Resetear sombras antes de dibujar
        this.ctx.shadowColor = 'transparent';
        this.ctx.shadowBlur = 0;
        
        // Aplicar efectos de brillo si están definidos
        if (this.theme.ball?.glow) {
            this.ctx.shadowColor = this.theme.ball.color;
            this.ctx.shadowBlur = 10;
        }
        
        this.ctx.beginPath();
        this.ctx.arc(this.ballX, this.ballY, this.ballSize, 0, Math.PI * 2);
        this.ctx.fillStyle = this.theme.ball?.color || 'white';
        this.ctx.fill();
    }
    
    updateTheme(newTheme) {
        this.theme = newTheme;
    }
}
