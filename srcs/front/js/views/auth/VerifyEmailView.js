import AuthService from '../../services/AuthService.js';

export function VerifyEmailView(uidb64, token) {
    const app = document.getElementById('app');
    
    // Pantalla de carga con nuestro logo
    app.innerHTML = `
        <div class="hero-section">
            <div class="container">
                <div class="row justify-content-center">
                    <div class="col-md-6 col-lg-5">
                        <div class="card login-card">
                            <div class="card-body p-5 text-center">
                                <div id="verifyContent">
                                    <svg class="logo mb-4" width="64" height="64" viewBox="0 0 100 100">
                                        <rect x="10" y="40" width="10" height="20" fill="#fff" class="paddle">
                                            <animate attributeName="height" values="20;40;20" dur="1s" repeatCount="indefinite"/>
                                        </rect>
                                        <circle cx="50" cy="50" r="5" fill="#fff" class="ball">
                                            <animate attributeName="cx" values="50;52;50" dur="0.5s" repeatCount="indefinite"/>
                                            <animate attributeName="cy" values="50;48;50" dur="0.5s" repeatCount="indefinite"/>
                                        </circle>
                                        <rect x="80" y="40" width="10" height="20" fill="#fff" class="paddle">
                                            <animate attributeName="height" values="40;20;40" dur="1s" repeatCount="indefinite"/>
                                        </rect>
                                    </svg>
                                    <h3 class="text-light mb-4">Verificando tu email...</h3>
                                    <p class="text-muted">Esto solo tomará un momento</p>
                                </div>
                            </div>
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
                <div class="hero-section">
                    <div class="container">
                        <div class="row justify-content-center">
                            <div class="col-md-6 col-lg-5">
                                <div class="card login-card">
                                    <div class="card-body p-5 text-center">
                                        <svg class="logo mb-4" width="64" height="64" viewBox="0 0 100 100">
                                            <rect width="100" height="100" fill="none"/>
                                            <circle cx="50" cy="50" r="40" fill="none" stroke="#28a745" stroke-width="8"/>
                                            <path d="M30 50 L45 65 L70 35" stroke="#28a745" stroke-width="8" fill="none">
                                                <animate attributeName="stroke-dasharray" from="0,100" to="100,100" dur="1s" fill="freeze"/>
                                            </path>
                                        </svg>
                                        <h3 class="text-light mb-4">¡Email Verificado!</h3>
                                        <div class="alert alert-success bg-success bg-opacity-25 text-light border-success mb-4">
                                            Tu cuenta ha sido verificada correctamente.
                                        </div>
                                        <div class="text-center">
                                            <a href="/login" class="btn btn-primary btn-lg">
                                                <i class="fas fa-sign-in-alt me-2"></i>Iniciar Sesión
                                            </a>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Limpiar cualquier estado anterior
            localStorage.clear();
            sessionStorage.clear();
        })
        .catch(error => {
            app.innerHTML = `
                <div class="hero-section">
                    <div class="container">
                        <div class="row justify-content-center">
                            <div class="col-md-6 col-lg-5">
                                <div class="card login-card">
                                    <div class="card-body p-5 text-center">
                                        <svg class="logo mb-4" width="64" height="64" viewBox="0 0 100 100">
                                            <rect width="100" height="100" fill="none"/>
                                            <circle cx="50" cy="50" r="40" fill="none" stroke="#dc3545" stroke-width="8"/>
                                            <path d="M35 35 L65 65 M65 35 L35 65" stroke="#dc3545" stroke-width="8" fill="none">
                                                <animate attributeName="stroke-dasharray" from="0,100" to="100,100" dur="1s" fill="freeze"/>
                                            </path>
                                        </svg>
                                        <h3 class="text-light mb-4">Error de Verificación</h3>
                                        <div class="alert alert-danger bg-danger bg-opacity-25 text-light border-danger mb-4">
                                            ${error.message}
                                        </div>
                                        <a href="/" data-link class="btn btn-primary btn-lg">
                                            <i class="fas fa-home me-2"></i>Volver al Inicio
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
}
