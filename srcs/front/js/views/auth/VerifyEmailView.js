import AuthService from '../../services/AuthService.js';

export function VerifyEmailView(uidb64, token) {
    const app = document.getElementById('app');
    
    // Mostrar pantalla de carga inmediatamente
    app.innerHTML = `
        <div class="container mt-4">
            <div class="card">
                <div class="card-body text-center">
                    <div id="verifyContent">
                        <h3 class="mb-4">Verificando tu email...</h3>
                        <div class="spinner-border text-primary mb-4" role="status">
                            <span class="visually-hidden">Cargando...</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Intentar verificar el email
    AuthService.verifyEmail(uidb64, token)
        .then(result => {
            app.innerHTML = `
                <div class="container mt-4">
                    <div class="card">
                        <div class="card-body text-center">
                            <i class="fas fa-check-circle text-success fa-4x mb-3"></i>
                            <h3 class="mb-4">¡Email Verificado!</h3>
                            <div class="alert alert-success mb-4">
                                Tu cuenta ha sido verificada correctamente.
                            </div>
                            <a href="/login" data-link class="btn btn-primary btn-lg">
                                Ir a Login
                            </a>
                        </div>
                    </div>
                </div>
            `;
        })
        .catch(error => {
            app.innerHTML = `
                <div class="container mt-4">
                    <div class="card">
                        <div class="card-body text-center">
                            <i class="fas fa-times-circle text-danger fa-4x mb-3"></i>
                            <h3 class="mb-4">Error de Verificación</h3>
                            <div class="alert alert-danger mb-4">
                                ${error.message}
                            </div>
                            <a href="/" data-link class="btn btn-primary btn-lg">
                                Volver al Inicio
                            </a>
                        </div>
                    </div>
                </div>
            `;
        });
}
