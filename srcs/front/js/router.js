// Importar solo los módulos que existen por ahora
import { LoginView } from '/js/views/auth/LoginView.js';
import { RegisterView } from '/js/views/auth/RegisterView.js';
import { VerifyEmailView } from '/js/views/auth/VerifyEmailView.js';  // Nuevo
import { UserView } from '/js/views/user/UserView.js';  // Nueva importación

class Router {
    routes = {
        '/': () => {
            const app = document.getElementById('app');
            app.innerHTML = `
                <div class="container mt-4">
                    <h1>Home</h1>
                    <nav>
                        <a href="/" data-link class="btn btn-primary me-2">Home</a>
                        <a href="/login" data-link class="btn btn-primary me-2">Login</a>
                        <a href="/register" data-link class="btn btn-primary">Register</a>
                    </nav>
                </div>
            `;
        },
        '/login': LoginView,
        '/register': RegisterView,
        '/verify-email/:uid/:token': VerifyEmailView,  // Nueva ruta para verificación
        '/user': UserView,      // Nueva ruta
        '/user/': UserView,     // También manejar con slash final
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
        const path = window.location.pathname || '/';
        console.log('Ruta inicial:', path);  // Debug

        // Verificar email en la carga inicial también
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

        const route = this.routes[path] || this.routes['/'];
        route();
    }

    handleRoute() {
        const path = window.location.pathname;
        console.log('Ruta actual:', path);

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

        const normalizedPath = path.endsWith('/') ? path.slice(0, -1) : path;
        const route = this.routes[normalizedPath] || this.routes['/404'];
        route();
    }

    navigateTo(url) {
        window.history.pushState(null, null, url);
        this.handleRoute();
    }
}

export default Router;
