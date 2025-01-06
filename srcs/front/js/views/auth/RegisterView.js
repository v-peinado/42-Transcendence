import AuthService from '../../services/AuthService.js';

export function RegisterView() {
    const app = document.getElementById('app');
    app.innerHTML = `
        <div class="container mt-4">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h3 class="card-title text-center">Registro</h3>
                            <div id="registerAlert"></div>
                            <form id="registerForm">
                                <div class="mb-3">
                                    <label for="username" class="form-label">Username</label>
                                    <input type="text" class="form-control" id="username" autocomplete="username" required>
                                </div>
                                <div class="mb-3">
                                    <label for="email" class="form-label">Email</label>
                                    <input type="email" class="form-control" id="email" autocomplete="email" required>
                                </div>
                                <div class="mb-3">
                                    <label for="password" class="form-label">Password</label>
                                    <input type="password" class="form-control" id="password" autocomplete="new-password" required>
                                </div>
                                <div class="mb-3">
                                    <label for="password2" class="form-label">Confirmar Password</label>
                                    <input type="password" class="form-control" id="password2" autocomplete="new-password" required>
                                </div>
                                <div class="mb-3 form-check">
                                    <input type="checkbox" class="form-check-input" id="privacy_policy" required>
                                    <label class="form-check-label" for="privacy_policy">
                                        Acepto la <a href="/privacy-policy" data-link>política de privacidad</a>
                                    </label>
                                </div>
                                <div class="d-grid gap-2">
                                    <button type="submit" class="btn btn-primary">Registrarse</button>
                                    <a href="/login" data-link class="btn btn-outline-secondary">¿Ya tienes cuenta? Login</a>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

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
