import { getNavbarHTML } from '../components/Navbar.js';
import AuthService from '../services/AuthService.js';

export async function NotFoundView() {
	const app = document.getElementById('app');
	const path = window.location.pathname;

	// Comprobar si es una URL de juego
	const gameMatch = path.match(/^\/game\/(\d+)$/);
	if (gameMatch && localStorage.getItem('isAuthenticated') === 'true') {
		// Si parece una URL de juego y el usuario está autenticado, 
		// intentar redirigir en lugar de mostrar 404
		const gameId = gameMatch[1];
		console.log('Redirigiendo a partida desde NotFoundView:', gameId);

		// Usar GameMatchView directamente
		const GameMatchView = (await import('./game/GameMatchView.js')).GameMatchView;
		GameMatchView(gameId);
		return;
	}

	// Si no es una URL de juego, mostrar 404 normal
	const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
	const userInfo = isAuthenticated ? await AuthService.getUserProfile() : null;
	const navbarHtml = await getNavbarHTML(isAuthenticated, userInfo);

	app.innerHTML = `
        ${navbarHtml}
        <div class="not-found-page">
            <div class="not-found-content">
                <h1 class="error-title">404</h1>
                <p class="error-subtitle">¡Ups! Parece que esta página tiene migrañas</p>
                
                <div class="pong-container">
                    <div class="paddle paddle-left"></div>
                    <div class="ball"></div>
                    <div class="paddle paddle-right"></div>
                </div>
                
                <a href="/" class="btn btn-lg btn-primary mt-4">
                    <i class="fas fa-home me-2"></i>
                    Volver al inicio
                </a>
            </div>
        </div>
    `;
}
