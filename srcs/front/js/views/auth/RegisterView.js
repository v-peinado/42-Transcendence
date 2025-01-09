import AuthService from '../../services/AuthService.js';

export function RegisterView() {
    const app = document.getElementById('app');
    app.innerHTML = `
        <div class="hero-section">
            <div class="container">
                <div class="row justify-content-center">
                    <div class="col-md-6 col-lg-5">
                        <div class="card login-card">
                            <div class="card-body p-5">
                                <div class="text-center mb-4">
                                    <svg class="logo mb-3" width="64" height="64" viewBox="0 0 100 100" id="registerLogo">
                                        <rect x="10" y="40" width="10" height="20" fill="#fff" class="paddle"/>
                                        <circle cx="50" cy="50" r="5" fill="#fff" class="ball"/>
                                        <rect x="80" y="40" width="10" height="20" fill="#fff" class="paddle"/>
                                    </svg>
                                    <h2 class="fw-bold">Crear Cuenta</h2>
                                    <p class="text-muted">Únete a la comunidad de Pong</p>
                                </div>
                                
                                <div id="registerAlert"></div>
                                
                                <form id="registerForm">
                                    <div class="form-floating mb-3">
                                        <input type="text" class="form-control bg-dark text-light" 
                                               id="username" placeholder="username" required>
                                        <label for="username">Username</label>
                                    </div>
                                    <div class="form-floating mb-3">
                                        <input type="email" class="form-control bg-dark text-light" 
                                               id="email" placeholder="name@example.com" required>
                                        <label for="email">Email</label>
                                    </div>
                                    <div class="form-floating mb-3">
                                        <input type="password" class="form-control bg-dark text-light" 
                                               id="password" placeholder="Password" required>
                                        <label for="password">Password</label>
                                    </div>
                                    <div class="form-floating mb-3">
                                        <input type="password" class="form-control bg-dark text-light" 
                                               id="password2" placeholder="Confirm Password" required>
                                        <label for="password2">Confirmar Password</label>
                                    </div>
                                    <div class="form-check mb-3">
                                        <input type="checkbox" class="form-check-input" id="privacy_policy" required>
                                        <label class="form-check-label text-light" for="privacy_policy">
                                            Acepto la <a href="/privacy-policy" data-link class="text-primary">política de privacidad</a>
                                        </label>
                                    </div>
                                    <button class="w-100 btn btn-lg btn-primary mb-3" type="submit">
                                        <i class="fas fa-user-plus me-2"></i>Registrarse
                                    </button>
                                    <div class="text-center">
                                        <a href="/login" data-link class="text-light">
                                            ¿Ya tienes cuenta? Inicia sesión
                                        </a>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Añadir evento para activar animación
    const form = document.getElementById('registerForm');
    const logo = document.getElementById('registerLogo');
    
    form.addEventListener('focusin', () => {
        logo.classList.add('animated');
    });

    form.addEventListener('focusout', (e) => {
        if (!form.contains(document.activeElement)) {
            logo.classList.remove('animated');
        }
    });

    document.getElementById('registerForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const alertDiv = document.getElementById('registerAlert');
        
        const password = document.getElementById('password').value;
        const password2 = document.getElementById('password2').value;
        const privacyAccepted = document.getElementById('privacy_policy').checked;
        
        if (!privacyAccepted) {
            alertDiv.innerHTML = `
                <div class="alert alert-danger">
                    Debes aceptar la política de privacidad para registrarte
                </div>
            `;
            return;
        }

        if (password !== password2) {
            alertDiv.innerHTML = `
                <div class="alert alert-danger">
                    Las contraseñas no coinciden
                </div>
            `;
            return;
        }

        try {
            const result = await AuthService.register({
                username: document.getElementById('username').value,
                email: document.getElementById('email').value,
                password: password,       // Se enviará como password1
                password2: password2,     // Se enviará como password2
                privacy_policy: privacyAccepted
            });

            alertDiv.innerHTML = `
                <div class="alert alert-success">
                    ${result.message}
                    <div class="mt-3">
                        <p>Por favor, revisa tu email para verificar tu cuenta.</p>
                        <a href="/login" data-link class="btn btn-primary mt-2">Ir a Login</a>
                    </div>
                </div>
            `;
        } catch (error) {
            alertDiv.innerHTML = `
                <div class="alert alert-danger">
                    ${error.message}
                </div>
            `;
        }
    });
}
