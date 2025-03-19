import { BaseGame } from './BaseGame.js';

export class TournamentGame extends BaseGame {
    constructor(canvas, matchInfo, maxPoints, onGameEnd) {
        super(canvas, maxPoints, onGameEnd);
        
        // Handler para prevenir scroll
        this.handleKeyDown = (e) => {
            if([38, 40].includes(e.keyCode)) {
                e.preventDefault();
            }
        };
        
        // Añadir event listener
        window.addEventListener('keydown', this.handleKeyDown);
        
        this.matchInfo = matchInfo;

        // Inicializar fullscreen
        this.setupFullscreen();

        // Configurar nombres y controles en el tablero
        document.querySelector('#leftPlayerName').textContent = matchInfo.player1.username;
        document.querySelector('#rightPlayerName').textContent = matchInfo.player2.username;
        
        // Mostrar los controles en la UI
        document.querySelector('.player-name-display:first-child .player-controls').innerHTML = `
            <span class="control-key">W</span>
            <span class="control-key">S</span>
        `;
        document.querySelector('.player-name-display:last-child .player-controls').innerHTML = `
            <span class="control-key">↑</span>
            <span class="control-key">↓</span>
        `;
    }

    // Añadir método para fullscreen
    setupFullscreen() {
        this.fullscreenBtn = document.getElementById('fullscreenBtn');
        this.gameWrapper = document.querySelector('.game-wrapper');

        if (this.fullscreenBtn) {
            this.fullscreenBtn.addEventListener('click', () => {
                if (!document.fullscreenElement) {
                    if (this.gameWrapper.requestFullscreen) {
                        this.gameWrapper.requestFullscreen();
                    } else if (this.gameWrapper.webkitRequestFullscreen) {
                        this.gameWrapper.webkitRequestFullscreen();
                    } else if (this.gameWrapper.msRequestFullscreen) {
                        this.gameWrapper.msRequestFullscreen();
                    }
                    this.gameWrapper.classList.add('fullscreen');
                    this.fullscreenBtn.innerHTML = '<i class="fas fa-compress"></i>';
                } else {
                    if (document.exitFullscreen) {
                        document.exitFullscreen();
                    } else if (document.webkitExitFullscreen) {
                        document.webkitExitFullscreen();
                    } else if (document.msExitFullscreen) {
                        document.msExitFullscreen();
                    }
                    this.gameWrapper.classList.remove('fullscreen');
                    this.fullscreenBtn.innerHTML = '<i class="fas fa-expand"></i>';
                }
            });

            // Manejar cambios de pantalla completa
            document.addEventListener('fullscreenchange', this.handleFullscreenChange.bind(this));
            document.addEventListener('webkitfullscreenchange', this.handleFullscreenChange.bind(this));
            document.addEventListener('mozfullscreenchange', this.handleFullscreenChange.bind(this));
            document.addEventListener('MSFullscreenChange', this.handleFullscreenChange.bind(this));
        }
    }

    handleFullscreenChange() {
        if (!document.fullscreenElement && 
            !document.webkitFullscreenElement && 
            !document.mozFullScreenElement && 
            !document.msFullscreenElement) {
            this.gameWrapper.classList.remove('fullscreen');
            this.fullscreenBtn.innerHTML = '<i class="fas fa-expand"></i>';
        }
    }

    update(timestamp) {
        this.ball.update();
        
        // Control para ambos jugadores
        if (this.keys[this.KEY_W]) this.leftPaddle.move(-1);
        if (this.keys[this.KEY_S]) this.leftPaddle.move(1);
        if (this.keys[this.KEY_UP]) this.rightPaddle.move(-1);
        if (this.keys[this.KEY_DOWN]) this.rightPaddle.move(1);

        this.handleCollisions();
        this.checkScore();
        this.updateGameState();
    }

    destroy() {
        // Eliminar event listeners de fullscreen
        document.removeEventListener('fullscreenchange', this.handleFullscreenChange);
        document.removeEventListener('webkitfullscreenchange', this.handleFullscreenChange);
        document.removeEventListener('mozfullscreenchange', this.handleFullscreenChange);
        document.removeEventListener('MSFullscreenChange', this.handleFullscreenChange);
        
        // Eliminar event listener al destruir el juego
        window.removeEventListener('keydown', this.handleKeyDown);
        super.destroy(); // Si existe un método destroy en la clase padre
    }
}
