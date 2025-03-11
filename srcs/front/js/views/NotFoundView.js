import { getNavbarHTML } from '../components/Navbar.js';
import AuthService from '../services/AuthService.js';
import GameService from '../services/GameService.js';
import { diagnosticService } from '../services/DiagnosticService.js';

export async function NotFoundView() {
	console.log('NotFoundView cargada');
	const app = document.getElementById('app');
	const path = window.location.pathname;

	// Comprobar si es una URL de juego
	const gameMatch = path.match(/^\/game\/(\d+)$/);
	if (gameMatch && localStorage.getItem('isAuthenticated') === 'true') {
		// Si parece una URL de juego y el usuario está autenticado, 
		// intentar verificar si es válida antes de redirigir
		const gameId = gameMatch[1];
		console.log(`Verificando partida ${gameId} antes de redirigir`);

		try {
			// Verificar si el usuario está autenticado
			const userId = await AuthService.getUserId();
			if (!userId) {
				console.warn('Usuario no autenticado');
				throw new Error('Usuario no autenticado');
			}

			// Verificar si la partida existe y si tiene acceso
			const gameAccess = await GameService.verifyGameAccess(gameId);

			// Añadir botón de diagnóstico independientemente del resultado de la verificación
			const diagnosticButton = document.createElement('button');
			diagnosticButton.id = 'emergencyDiagnostic';
			diagnosticButton.className = 'btn btn-danger position-fixed';
			diagnosticButton.style.bottom = '20px';
			diagnosticButton.style.right = '20px';
			diagnosticButton.style.zIndex = '9999';
			diagnosticButton.innerHTML = '<i class="fas fa-stethoscope"></i> Diagnóstico de Emergencia';
			diagnosticButton.onclick = () => diagnosticService.showDiagnosticPanel();
			document.body.appendChild(diagnosticButton);

			// Si tenemos datos de reconexión en localStorage, intentar reconectar sin verificar API
			const savedGameData = localStorage.getItem(`game_${gameId}`);
			if (savedGameData) {
				console.log('Encontrados datos de reconexión guardados', JSON.parse(savedGameData));

				// Intentar cargar la vista de juego directamente
				const GameMatchView = (await import('./game/GameMatchView.js')).GameMatchView;
				GameMatchView(gameId);
				return;
			}

			if (gameAccess.exists && gameAccess.can_access) {
				console.log('Partida válida, redirigiendo', gameAccess);

				// Usar GameMatchView directamente
				const GameMatchView = (await import('./game/GameMatchView.js')).GameMatchView;
				GameMatchView(gameId);
				return;
			} else {
				console.warn('Partida no válida o sin acceso', gameAccess);
				// No redirigir, mostrar 404 con botón de diagnóstico
			}
		} catch (error) {
			console.error('Error al cargar la partida', error);
			// Mantener el botón de diagnóstico incluso en caso de error
		}
	}

	// Si no es una URL de juego o hay error, mostrar 404 normal
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
                
                ${gameMatch ? `
                <button id="diagnosticBtn" class="btn btn-warning mt-3">
                    <i class="fas fa-stethoscope me-2"></i>Ver diagnóstico de conexión
                </button>
                ` : ''}
            </div>
        </div>
    `;

	// Añadir event listener para el botón de diagnóstico si existe
	const diagnosticBtn = document.getElementById('diagnosticBtn');
	if (diagnosticBtn) {
		diagnosticBtn.addEventListener('click', () => {
			diagnosticService.showDiagnosticPanel();
		});
	}
}
