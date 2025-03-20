export function initializeMenuAnimations() {
    const username = localStorage.getItem('username');
    document.getElementById('username-placeholder').textContent = username;

    setTimeout(() => {
        const welcomeMessage = document.querySelector('.welcome-message');
        const gameMenu = document.querySelector('.game-menu-container');
        
        // Forzar un reflow
        welcomeMessage.offsetHeight;
        gameMenu.offsetHeight;
        
        welcomeMessage.classList.add('fade-out');
        gameMenu.classList.add('slide-up');
    }, 1500); // Aumentado el tiempo de espera inicial
}
