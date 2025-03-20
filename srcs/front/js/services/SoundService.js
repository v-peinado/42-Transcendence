class SoundService {
    constructor() {
        this.sounds = {
            matchFound: new Audio('/sounds/match_found.mp3'),
            countdown: new Audio('/sounds/countdown.mp3'),
            victory: new Audio('/sounds/victory.mp3'),
            defeat: new Audio('/sounds/defeat.mp3')  // Añadir sonido de derrota
        };
    }

    init() {
        if (!this.audioContext) {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
    }

    async playMatchFound() {
        this.init();
        
        // Crear osciladores para un acorde alegre
        const baseOsc = this.audioContext.createOscillator();
        const thirdOsc = this.audioContext.createOscillator();
        const fifthOsc = this.audioContext.createOscillator();
        const mainGain = this.audioContext.createGain();
        
        // Configurar sonidos para un acorde mayor (Do-Mi-Sol)
        baseOsc.type = 'sine';
        thirdOsc.type = 'sine';
        fifthOsc.type = 'sine';
        
        // Frecuencias para Do mayor (C4-E4-G4)
        baseOsc.frequency.setValueAtTime(523.25, this.audioContext.currentTime);  // Do5
        thirdOsc.frequency.setValueAtTime(659.25, this.audioContext.currentTime); // Mi5
        fifthOsc.frequency.setValueAtTime(783.99, this.audioContext.currentTime); // Sol5
        
        // Configurar envolvente de volumen
        mainGain.gain.setValueAtTime(0, this.audioContext.currentTime);
        mainGain.gain.linearRampToValueAtTime(0.2, this.audioContext.currentTime + 0.1);
        mainGain.gain.linearRampToValueAtTime(0.2, this.audioContext.currentTime + 0.3);
        mainGain.gain.linearRampToValueAtTime(0, this.audioContext.currentTime + 0.6);
        
        // Conectar todo
        baseOsc.connect(mainGain);
        thirdOsc.connect(mainGain);
        fifthOsc.connect(mainGain);
        mainGain.connect(this.audioContext.destination);
        
        // Reproducir
        baseOsc.start();
        thirdOsc.start();
        fifthOsc.start();
        
        baseOsc.stop(this.audioContext.currentTime + 0.6);
        thirdOsc.stop(this.audioContext.currentTime + 0.6);
        fifthOsc.stop(this.audioContext.currentTime + 0.6);
    }

    async playCountdown() {
        this.init();
        
        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();
        
        // Sonido más agudo y corto para la cuenta atrás
        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(880, this.audioContext.currentTime); // La5
        
        gainNode.gain.setValueAtTime(0, this.audioContext.currentTime);
        gainNode.gain.linearRampToValueAtTime(0.2, this.audioContext.currentTime + 0.05);
        gainNode.gain.linearRampToValueAtTime(0, this.audioContext.currentTime + 0.2);
        
        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);
        
        oscillator.start();
        oscillator.stop(this.audioContext.currentTime + 0.2);
    }

    async playVictory() {
        try {
            await this.sounds.victory.play();
        } catch (error) {
            console.warn('Error reproduciendo sonido de victoria:', error);
        }
    }

    async playDefeat() {
        try {
            await this.sounds.defeat.play();
        } catch (error) {
            console.warn('Error reproduciendo sonido de derrota:', error);
        }
    }
}

export const soundService = new SoundService();
