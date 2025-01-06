import AuthService from '../../services/AuthService.js';

export function LoginView() {
    const app = document.getElementById('app');
    app.innerHTML = `
        <div class="container mt-4">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h3 class="card-title text-center">Login</h3>
                            <div id="loginAlert"></div>
                            <form id="loginForm">
                                <div class="mb-3">
                                    <label for="username" class="form-label">Username</label>
                                    <input type="text" class="form-control" id="username" autocomplete="username" required>
                                </div>
                                <div class="mb-3">
                                    <label for="password" class="form-label">Password</label>
                                    <input type="password" class="form-control" id="password" autocomplete="current-password" required>
                                </div>
                                <div class="mb-3 form-check">
                                    <input type="checkbox" class="form-check-input" id="remember">
                                    <label class="form-check-label" for="remember">Recordarme</label>
                                </div>
                                <div class="d-grid">
                                    <button type="submit" class="btn btn-primary">Login</button>
                                </div>
                                <div class="text-center mt-3">
                                    <a href="/register" data-link>¿No tienes cuenta? Regístrate</a>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    document.getElementById('loginForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const remember = document.getElementById('remember').checked;
        const alertDiv = document.getElementById('loginAlert');
        
        try {
            const result = await AuthService.login(username, password, remember);
            if (result.success) {
                window.location.href = result.redirectUrl;
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
