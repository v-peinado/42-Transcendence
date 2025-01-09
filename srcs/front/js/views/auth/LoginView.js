import AuthService from '../../services/AuthService.js';

export function LoginView() {
    const app = document.getElementById('app');
    app.innerHTML = `
        <div class="hero-section">
            <div class="container">
                <div class="row justify-content-center">
                    <div class="col-md-6 col-lg-5">
                        <div class="card login-card">
                            <div class="card-body p-5">
                                <div class="text-center mb-4">
                                    <svg class="logo mb-3" width="64" height="64" viewBox="0 0 100 100" id="loginLogo">
                                        <rect x="10" y="40" width="10" height="20" fill="#fff" class="paddle"/>
                                        <circle cx="50" cy="50" r="5" fill="#fff" class="ball"/>
                                        <rect x="80" y="40" width="10" height="20" fill="#fff" class="paddle"/>
                                    </svg>
                                    <h2 class="fw-bold">Iniciar Sesión</h2>
                                    <p class="text-muted">Accede a tu cuenta para jugar</p>
                                </div>
                                
                                <div id="loginAlert"></div>
                                
                                <form id="loginForm">
                                    <div class="form-floating mb-3">
                                        <input type="text" class="form-control bg-dark text-light" 
                                               id="username" placeholder="Username" required>
                                        <label for="username">Username</label>
                                    </div>
                                    
                                    <div class="form-floating mb-3">
                                        <input type="password" class="form-control bg-dark text-light" 
                                               id="password" placeholder="Password" required>
                                        <label for="password">Password</label>
                                    </div>
                                    
                                    <div class="form-check mb-3">
                                        <input type="checkbox" class="form-check-input" id="remember">
                                        <label class="form-check-label text-light" for="remember">
                                            Recordarme
                                        </label>
                                    </div>
                                    
                                    <button class="w-100 btn btn-lg btn-primary mb-3" type="submit">
                                        <i class="fas fa-sign-in-alt me-2"></i>Iniciar Sesión
                                    </button>
                                    
                                    <div class="text-center">
                                        <a href="/register" data-link class="text-light">
                                            ¿No tienes cuenta? Regístrate
                                        </a>
                                    </div>
                                </form>
                                
                                <div class="text-center mt-3">
                                    <a href="/reset_password" data-link class="text-light text-decoration-none">
                                        <i class="fas fa-key me-1"></i>¿Olvidaste tu contraseña?
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Añadir evento para activar animación
    const form = document.getElementById('loginForm');
    const logo = document.getElementById('loginLogo');
    
    form.addEventListener('focusin', () => {
        logo.classList.add('animated');
    });

    form.addEventListener('focusout', (e) => {
        // Solo desactivar si no hay ningún elemento del form enfocado
        if (!form.contains(document.activeElement)) {
            logo.classList.remove('animated');
        }
    });

    document.getElementById('loginForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const remember = document.getElementById('remember').checked;
        const alertDiv = document.getElementById('loginAlert');
        
        try {
            const result = await AuthService.login(username, password, remember);
            if (result.success) {
                localStorage.setItem('isAuthenticated', 'true');
                localStorage.setItem('username', username);
                window.location.href = '/profile';  // Cambiar a perfil en lugar de /user
            } else if (result.needsEmailVerification) {
                alertDiv.innerHTML = `
                    <div class="alert alert-warning">
                        <p>${result.message}</p>
                        <div class="mt-3">
                            <p>Por favor, revisa tu email para activar tu cuenta.</p>
                            <p class="text-muted small">¿No recibiste el email? 
                                <a href="/resend-verification" data-link>Reenviar email de verificación</a>
                            </p>
                            <a href="/" data-link class="btn btn-primary mt-2">Volver al inicio</a>
                        </div>
                    </div>
                `;
            } else if (result.pending2FA) {
                alertDiv.innerHTML = `
                    <div class="alert alert-warning">
                        ${result.message}
                    </div>
                `;
            }
        } catch (error) {
            alertDiv.innerHTML = `
                <div class="alert alert-danger">
                    <p>${error.message}</p>
                    <div class="mt-3">
                        <a href="/register" data-link class="btn btn-outline-primary">Registrarse</a>
                        <a href="/" data-link class="btn btn-secondary">Volver al inicio</a>
                    </div>
                </div>
            `;
        }
    });
}
