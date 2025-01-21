// Importar solo los módulos que existen por ahora
import { LoginView } from '/js/views/auth/LoginView.js';
import { RegisterView } from '/js/views/auth/RegisterView.js';
import { VerifyEmailView } from '/js/views/auth/VerifyEmailView.js';  // Nuevo
import { VerifyEmailChangeView } from '/js/views/auth/VerifyEmailChangeView.js';  // Nueva importación
import { UserView } from '/js/views/user/UserView.js';  // Nueva importación
import { UserProfileView } from '/js/views/user/UserProfileView.js';  // Nueva importación
import { RequestPasswordResetView } from '/js/views/auth/RequestPasswordResetView.js';
import { ResetPasswordView } from '/js/views/auth/ResetPasswordView.js';
import { GDPRSettingsView } from '/js/views/user/GDPRSettingsView.js';

class Router {
    routes = {
        '/': () => {
            const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
            const username = localStorage.getItem('username');
            const app = document.getElementById('app');
            app.innerHTML = `
                <!-- Navbar con nuevo logo -->
                <nav class="navbar navbar-expand-lg navbar-dark bg-dark fixed-top">
                    <div class="container">
                        <a class="navbar-brand d-flex align-items-center" href="/" data-link>
                            <svg class="logo me-2" width="32" height="32" viewBox="0 0 100 100">
                                <rect x="10" y="40" width="10" height="20" fill="#fff">
                                    <animate attributeName="height" values="20;40;20" dur="1s" repeatCount="indefinite"/>
                                </rect>
                                <circle cx="50" cy="50" r="5" fill="#fff">
                                    <animate attributeName="cx" values="50;52;50" dur="0.5s" repeatCount="indefinite"/>
                                    <animate attributeName="cy" values="50;48;50" dur="0.5s" repeatCount="indefinite"/>
                                </circle>
                                <rect x="80" y="40" width="10" height="20" fill="#fff">
                                    <animate attributeName="height" values="40;20;40" dur="1s" repeatCount="indefinite"/>
                                </rect>
                            </svg>
                            <span class="brand-text">Transcendence</span>
                        </a>
                        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                            <span class="navbar-toggler-icon"></span>
                        </button>
                        <div class="collapse navbar-collapse" id="navbarNav">
                            <ul class="navbar-nav me-auto">
                                <li class="nav-item">
                                    <a class="nav-link" href="/game" data-link>
                                        <i class="fas fa-play me-1"></i>Jugar
                                    </a>
                                </li>
                                <li class="nav-item">
                                    <a class="nav-link" href="/leaderboard" data-link>
                                        <i class="fas fa-trophy me-1"></i>Clasificación
                                    </a>
                                </li>
                            </ul>
                            <!-- Menú para usuarios autenticados -->
                            ${isAuthenticated ? `
                                <ul class="navbar-nav">
                                    <li class="nav-item">
                                        <a class="nav-link" href="/chat" data-link>
                                            <i class="fas fa-comments me-1"></i>Chat
                                        </a>
                                    </li>
                                    <li class="nav-item dropdown">
                                        <a class="nav-link dropdown-toggle d-flex align-items-center gap-2" href="#" role="button" 
                                           data-bs-toggle="dropdown" aria-expanded="false">
                                            <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=${username}" 
                                                 alt="Avatar" class="rounded-circle" width="32" height="32">
                                            <span>${username}</span>
                                        </a>
                                        <ul class="dropdown-menu dropdown-menu-end">
                                            <li class="px-3 py-2 d-flex align-items-center bg-dark-subtle">
                                                <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=${username}" 
                                                     alt="Avatar" class="rounded-circle me-2" width="48" height="48">
                                                <div class="text-truncate">
                                                    <div class="fw-bold">${username}</div>
                                                    <small class="text-muted">Ver perfil</small>
                                                </div>
                                            </li>
                                            <li><hr class="dropdown-divider"></li>
                                            <li>
                                                <a class="dropdown-item" href="/profile" data-link>
                                                    <i class="fas fa-user me-2"></i>Perfil
                                                </a>
                                            </li>
                                            <li>
                                                <a class="dropdown-item" href="/settings" data-link>
                                                    <i class="fas fa-cog me-2"></i>Configuración
                                                </a>
                                            </li>
                                            <li>
                                                <a class="dropdown-item" href="/gdpr-settings" data-link>
                                                    <i class="fas fa-shield-alt me-2"></i>Privacidad
                                                </a>
                                            </li>
                                            <li><hr class="dropdown-divider"></li>
                                            <li>
                                                <button class="dropdown-item text-danger" id="logoutBtn">
                                                    <i class="fas fa-sign-out-alt me-2"></i>Cerrar Sesión
                                                </button>
                                            <li>
                                                <button class="dropdown-item text-danger" id="logoutBtn">
                                                    <i class="fas fa-sign-out-alt me-2"></i>Cerrar Sesión
                                                </button>
                                            </li>
                                        </ul>
                                    </li>
                                </ul>
                            ` : `
                                <ul class="navbar-nav">
                                    <li class="nav-item">
                                        <a class="nav-link" href="/login" data-link>
                                            <i class="fas fa-sign-in-alt me-1"></i>Login
                                        </a>
                                    </li>
                                    <li class="nav-item">
                                        <a class="nav-link" href="/register" data-link>
                                            <i class="fas fa-user-plus me-1"></i>Registro
                                        </a>
                                    </li>
                                </ul>
                            `}
                        </div>
                    </div>
                </nav>

                <!-- Hero Section con nueva estructura -->
                <main>
                    <div class="hero-section">
                        <div class="hero-content">
                            <div class="container">
                                <div class="row justify-content-center">
                                    <div class="col-lg-8 text-center">
                                        <h1 class="display-4 fw-bold mb-4">¡Bienvenido a Transcendence!</h1>
                                        <p class="lead mb-4">El clásico juego de Pong reinventado para la web moderna</p>
                                        <div class="d-grid gap-2 d-sm-flex justify-content-sm-center mb-5">
                                            <a href="/login" data-link class="btn btn-primary btn-lg px-4 me-sm-3">
                                                <i class="fas fa-play me-2"></i>Empezar a Jugar
                                            </a>
                                            <a href="/register" data-link class="btn btn-outline-light btn-lg px-4">
                                                <i class="fas fa-user-plus me-2"></i>Registrarse
                                            </a>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Features Section con nuevo fondo -->
                    <div class="features-section">
                        <div class="container">
                            <div class="row g-4 py-5 row-cols-1 row-cols-lg-3">
                                <div class="col d-flex align-items-start">
                                    <div class="icon-square text-body-emphasis bg-body-secondary d-inline-flex align-items-center justify-content-center fs-4 flex-shrink-0 me-3">
                                        <i class="fas fa-gamepad"></i>
                                    </div>
                                    <div>
                                        <h3 class="fs-2">Juega Online</h3>
                                        <p>Compite contra otros jugadores en tiempo real.</p>
                                    </div>
                                </div>
                                <div class="col d-flex align-items-start">
                                    <div class="icon-square text-body-emphasis bg-body-secondary d-inline-flex align-items-center justify-content-center fs-4 flex-shrink-0 me-3">
                                        <i class="fas fa-trophy"></i>
                                    </div>
                                    <div>
                                        <h3 class="fs-2">Clasificación</h3>
                                        <p>Compite por los primeros puestos del ranking.</p>
                                    </div>
                                </div>
                                <div class="col d-flex align-items-start">
                                    <div class="icon-square text-body-emphasis bg-body-secondary d-inline-flex align-items-center justify-content-center fs-4 flex-shrink-0 me-3">
                                        <i class="fas fa-users"></i>
                                    </div>
                                    <div>
                                        <h3 class="fs-2">Comunidad</h3>
                                        <p>Únete a una comunidad activa de jugadores.</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </main>
            `;

            // Agregar evento de logout si el usuario está autenticado
            if (isAuthenticated) {
                document.getElementById('logoutBtn')?.addEventListener('click', async () => {
                    try {
                        await AuthService.logout();
                        localStorage.removeItem('isAuthenticated');
                        window.location.href = '/login';
                    } catch (error) {
                        console.error('Error en logout:', error);
                    }
                });
            }
        },
        '/login': LoginView,
        '/register': RegisterView,
        '/verify-email/:uid/:token': VerifyEmailView,  // Nueva ruta para verificación
        '/verify-email-change/:uid/:token': VerifyEmailChangeView,  // Añadir esta ruta
        '/verify-email-change/:uid/:token/': VerifyEmailChangeView,  // Añadir slash final
        '/user': UserView,      // Nueva ruta
        '/user/': UserView,     // También manejar con slash final
        '/profile': UserProfileView,  // Nueva ruta para perfil
        '/profile/': UserProfileView, // También manejar con slash final
        '/reset_password': RequestPasswordResetView,
        '/reset/:uid/:token': ResetPasswordView,
        '/gdpr-settings': GDPRSettingsView,
        '/gdpr-settings/': GDPRSettingsView,
        '/404': () => {
            const app = document.getElementById('app');
            app.innerHTML = `
                <div class="container mt-4">
                    <h1>404 - Página no encontrada</h1>
                    <a href="/" data-link class="btn btn-primary">Volver a Home</a>
                </div>
            `;
        }
    };

    constructor() {
        this.currentPath = window.location.pathname;
        this.handleInitialRoute();  // Manejar la ruta inicial explícitamente
        
        window.addEventListener('popstate', () => this.handleRoute());
        document.addEventListener('click', e => {
            if (e.target.matches('[data-link]')) {
                e.preventDefault();
                this.navigateTo(e.target.href);
            }
        });
    }

    handleInitialRoute() {
        const path = window.location.pathname + window.location.search;
        console.log('Ruta inicial completa:', path);  // Debug

        // Manejar código de 42 primero
        const searchParams = new URLSearchParams(window.location.search);
        const code = searchParams.get('code');

        if (path.startsWith('/login') && code) {
            // Render inmediato de LoginView
            LoginView();
            return;
        }

        // Manejar verificación de email
        if (path.includes('/verify-email/')) {
            const parts = path.split('/verify-email/')[1].split('/');
            if (parts.length >= 2) {
                const uidb64 = parts[0];
                const token = parts[1].replace('/', '');
                console.log('Verificando email (inicial):', { uidb64, token });
                VerifyEmailView(uidb64, token);
                return;
            }
        }

        // Verificar cambio de email
        if (path.includes('/verify-email-change/')) {
            const parts = path.split('/verify-email-change/')[1].split('/');
            if (parts.length >= 2) {
                const uidb64 = parts[0];
                const token = parts[1].replace('/', '');
                console.log('Verificando cambio de email:', { uidb64, token });
                VerifyEmailChangeView(uidb64, token);
                return;
            }
        }

        // Añadir manejo de reset de contraseña
        if (path.includes('/reset/')) {
            const parts = path.split('/reset/')[1].split('/');
            if (parts.length >= 2) {
                const uidb64 = parts[0];
                const token = parts[1];
                ResetPasswordView(uidb64, token);
                return;
            }
        }

        const normalizedPath = path.split('?')[0];
        const route = this.routes[normalizedPath] || this.routes['/404'];
        
        if (typeof route === 'function') {
            if (route.constructor.name === 'AsyncFunction') {
                route().catch(console.error);  // Manejar promesas rechazadas
            } else {
                route();
            }
        }
    }

    async handleRoute() {
        const path = window.location.pathname + window.location.search;  // Incluir query params
        console.log('Manejando ruta completa:', path);  // Debug
        
        // Reset data-page attribute
        document.body.removeAttribute('data-page');
        
        console.log('Ruta actual:', path);

        // Manejar login con código de 42
        if (path.startsWith('/login') && path.includes('code=')) {
            await LoginView();
            return;
        }

        // Manejar verificación de email sin redirección automática
        if (path.includes('/verify-email/')) {
            const parts = path.split('/verify-email/')[1].split('/');
            if (parts.length >= 2) {
                const uidb64 = parts[0];
                const token = parts[1].replace('/', '');
                console.log('Verificando email:', { uidb64, token });
                VerifyEmailView(uidb64, token);
                return;
            }
        }

        // Manejar verificación de cambio de email sin redirección automática
        if (path.includes('/verify-email-change/')) {
            const parts = path.split('/verify-email-change/')[1].split('/');
            if (parts.length >= 2) {
                const uidb64 = parts[0];
                const token = parts[1];  // Quitar el replace('/', '') porque necesitamos el slash
                console.log('Verificando cambio de email:', { uidb64, token });
                VerifyEmailChangeView(uidb64, token);
                return;
            }
        }

        const normalizedPath = path.split('?')[0];  // Eliminar query params para matching
        const route = this.routes[normalizedPath] || this.routes['/404'];
        
        if (typeof route === 'function') {
            if (route.constructor.name === 'AsyncFunction') {
                await route();
            } else {
                route();
            }
        }
    }

    navigateTo(url) {
        window.history.pushState(null, null, url);
        this.handleRoute();
    }
}

export default Router;

