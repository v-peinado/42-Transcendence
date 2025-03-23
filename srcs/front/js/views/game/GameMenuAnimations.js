export function initializeMenuAnimations() {
    const welcomeMessage = document.querySelector('.welcome-message');
    const menuContainer = document.querySelector('.game-menu-container');

    // Añadir las clases para las animaciones después de un breve retraso
    setTimeout(() => {
        if (welcomeMessage) {
            welcomeMessage.classList.add('fade-out');
        }
        if (menuContainer) {
            menuContainer.classList.add('slide-up');
        }
    }, 500);
}
