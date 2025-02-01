// Importar solo los módulos que existen por ahora
import { LoginView } from '/js/views/auth/LoginView.js';
import { RegisterView } from '/js/views/auth/RegisterView.js';
import { VerifyEmailView } from '/js/views/auth/VerifyEmailView.js';  // Nuevo
import { VerifyEmailChangeView } from '/js/views/auth/VerifyEmailChangeView.js';  // Nueva importación
import { UserProfileView } from '/js/views/user/UserProfileView.js';  // Mantener solo UserProfileView
import { RequestPasswordResetView } from '/js/views/auth/RequestPasswordResetView.js';
import { ResetPasswordView } from '/js/views/auth/ResetPasswordView.js';
import { GDPRSettingsView } from '/js/views/user/GDPRSettingsView.js';
import { NotFoundView } from '/js/views/NotFoundView.js';  // Añadir esta importación al inicio con las otras
import AuthService from '/js/services/AuthService.js';
import { getNavbarHTML } from '/js/components/Navbar.js';

class Router {
    constructor() {
        // Solo limpiar sesión si NO estamos autenticados
        const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
        
        if (!isAuthenticated && (
            window.location.pathname === '/' || 
            window.location.pathname === '/login'
        )) {
            AuthService.clearSession().then(() => {
                setTimeout(() => {
                    this.handleInitialRoute();
                }, 100);
            });
            return;
        }
        
        this.handleInitialRoute();
        
        // Añadir manejo de navegación
        window.addEventListener('popstate', () => this.handleRoute());
        document.addEventListener('click', e => {
            if (e.target.matches('[data-link]')) {
                e.preventDefault();
                this.navigateTo(e.target.href);
            }
        });

        // Añadir event listener global para logout
        document.addEventListener('click', async (e) => {
            if (e.target && (e.target.classList.contains('logout-btn') || e.target.closest('.logout-btn'))) {
                e.preventDefault();
                try {
                    await AuthService.logout();
                    localStorage.clear();
                    sessionStorage.clear();
                    window.location.replace('/');
                } catch (error) {
                    console.error('Error en logout:', error);
                    // Intentar cerrar sesión de todas formas
                    localStorage.clear();
                    sessionStorage.clear();
                    window.location.replace('/');
                }
            }
        });
    }

    routes = {
        '/': async () => {
            const app = document.getElementById('app');
            const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
            
            if (isAuthenticated) {
                try {
                    const userInfo = await AuthService.getUserProfile();
                    if (userInfo && !userInfo.error) {
                        await this.renderHomePage(true, userInfo);
                        return;
                    }
                } catch (error) {
                    console.error('Error loading profile:', error);
                }
                // Si hay error, limpiar estado
                localStorage.clear();
                sessionStorage.clear();
            }
            // Si no está autenticado o hubo error, mostrar página no autenticada
            await this.renderHomePage(false);
        },
        '/login': LoginView,
        '/register': RegisterView,
        '/verify-email/:uid/:token': VerifyEmailView,  // Nueva ruta para verificación
        '/verify-email-change/:uid/:token': VerifyEmailChangeView,  // Añadir esta ruta
        '/verify-email-change/:uid/:token/': VerifyEmailChangeView,  // Añadir slash final
        '/profile': UserProfileView,  // Mantener solo la ruta de profile
        '/profile/': UserProfileView, // Con slash final también
        '/reset_password': RequestPasswordResetView,
        '/reset/:uid/:token': ResetPasswordView,
        '/gdpr-settings': GDPRSettingsView,
        '/gdpr-settings/': GDPRSettingsView,
        '/404': NotFoundView,  // Reemplazar la función anónima existente con NotFoundView
    };

    async renderHomePage(isAuthenticated, userInfo = null) {
        const app = document.getElementById('app');
        
        if (!isAuthenticated) {
            app.innerHTML = `
                ${getNavbarHTML(false)}
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
                                <div class="col">
                                    <div class="feature-item">
                                        <div class="feature-icon">
                                            <i class="fas fa-gamepad"></i>
                                        </div>
                                        <h3>Juega Online</h3>
                                        <p>Compite contra otros jugadores en tiempo real con nuestro sistema de matchmaking avanzado.</p>
                                    </div>
                                </div>
                                <div class="col">
                                    <div class="feature-item">
                                        <div class="feature-icon">
                                            <i class="fas fa-trophy"></i>
                                        </div>
                                        <h3>Clasificación</h3>
                                        <p>Escala posiciones en nuestro ranking competitivo y demuestra que eres el mejor jugador.</p>
                                    </div>
                                </div>
                                <div class="col">
                                    <div class="feature-item">
                                        <div class="feature-icon">
                                            <i class="fas fa-users"></i>
                                        </div>
                                        <h3>Comunidad</h3>
                                        <p>Únete a una comunidad activa de jugadores, haz amigos y participa en torneos exclusivos.</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </main>
            `;
        } else {
            app.innerHTML = `
                ${getNavbarHTML(true, userInfo)}
                <div class="hero-section">
                    <div class="container">
                        <div class="row justify-content-center">
                            <div class="col-lg-8 text-center">
                                <h1 class="display-4 fw-bold">¡Hola, ${userInfo.username}!</h1>
                                <div class="mt-4">
                                    ${window.location.pathname === '/profile' ? `
                                        <div class="d-flex justify-content-center gap-3">
                                            <a href="/game" data-link class="btn btn-primary btn-lg">
                                                <i class="fas fa-gamepad me-2"></i>¡Jugar Ahora!
                                            </a>
                                            <button id="logoutBtn" class="btn btn-outline-danger btn-lg">
                                                <i class="fas fa-sign-out-alt me-2"></i>Cerrar Sesión
                                            </button>
                                        </div>
                                    ` : `
                                        <a href="/game" data-link class="btn btn-primary btn-lg">
                                            <i class="fas fa-gamepad me-2"></i>¡Jugar Ahora!
                                        </a>
                                    `}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // Configurar el botón de logout solo si estamos en la página de perfil
            if (window.location.pathname === '/profile') {
                document.getElementById('logoutBtn')?.addEventListener('click', async () => {
                    try {
                        await AuthService.logout();
                    } catch (error) {
                        console.error('Error en logout:', error);
                    } finally {
                        localStorage.clear();
                        sessionStorage.clear();
                        window.location.href = '/';
                    }
                });
            }
        }
    }

    async handleInitialRoute() {
        const path = window.location.pathname + window.location.search;
        console.log('Ruta inicial completa:', path);  // Debug

        // Si estamos en la página principal, verificar autenticación primero
        if (path === '/' || path === '') {
            const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
            if (isAuthenticated) {
                try {
                    const userInfo = await AuthService.getUserProfile();
                    if (userInfo && !userInfo.error) {
                        await this.renderHomePage(true, userInfo);
                        return;
                    }
                } catch (error) {
                    console.error('Error loading profile:', error);
                }
            }
            // Si no está autenticado o hay error, mostrar página normal
            await this.renderHomePage(false);
            return;
        }

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

        // Verificar rutas protegidas
        if (path.startsWith('/profile') && localStorage.getItem('isAuthenticated') !== 'true') {
            window.location.href = '/login';
            return;
        }

        // Verificar autenticación pendiente para rutas protegidas
        if (path.startsWith('/profile')) {
            if (sessionStorage.getItem('pendingAuth') === 'true') {
                // Redirigir de vuelta al login si hay auth pendiente
                window.location.replace('/login');
                return;
            }
            if (localStorage.getItem('isAuthenticated') !== 'true') {
                window.location.replace('/login');
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
        // Si es la página principal y el usuario está autenticado, forzar recarga
        if (url === '/' && localStorage.getItem('isAuthenticated') === 'true') {
            window.location.reload();
            return;
        }
        window.history.pushState(null, null, url);
        this.handleRoute();
    }
}


export default Router;
