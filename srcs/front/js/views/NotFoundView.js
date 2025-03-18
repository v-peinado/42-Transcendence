import { getNavbarHTML } from '../components/Navbar.js';

export async function NotFoundView() {
    const app = document.getElementById('app');
    
    app.innerHTML = `
        ${getNavbarHTML()}
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
