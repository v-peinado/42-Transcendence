import AuthService from '../../services/AuthService.js';

export function VerifyEmailChangeView(uid, token) {
    const app = document.getElementById('app');
    
    // Mostrar pantalla de carga
    app.innerHTML = `
        <div class="hero-section">
            <div class="container">
                <div class="row justify-content-center">
                    <div class="col-md-6 text-center">
                        <h3 class="text-light mb-4">Verificando cambio de email...</h3>
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Cargando...</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Verificar el cambio
    AuthService.verifyEmailChange(uid, token)
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
                                            <circle cx="50" cy="50" r="40" fill="none" stroke="#0d6efd" stroke-width="8">
                                                <animate attributeName="stroke-dasharray" from="0,251.2" to="251.2,0" dur="1s" fill="freeze"/>
                                            </circle>
                                            <path d="M30 50 L45 65 L70 35" stroke="#0d6efd" stroke-width="8" fill="none">
                                                <animate attributeName="stroke-dasharray" from="0,90" to="90,0" dur="0.5s" fill="freeze" begin="0.6s"/>
                                            </path>
                                        </svg>
                                        <h3 class="text-light mb-4">¡Email Actualizado!</h3>
                                        <p class="text-white mb-4">${result.message}</p>
                                        <a href="/profile" data-link class="btn btn-primary">
                                            Ir a mi perfil
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        })
        .catch(error => {
            let errorMessage;
            // Mensajes más amigables para el usuario
            if (error.message.includes('Token invalid')) {
                errorMessage = 'El enlace que intentas usar ya no es válido. Por favor, solicita un nuevo cambio de email desde tu perfil.';
            } else if (error.message.includes('Error sending email change')) {
                errorMessage = 'Ha ocurrido un error al procesar el cambio de email. Por favor, inténtalo de nuevo desde tu perfil.';
            } else {
                errorMessage = 'Ha ocurrido un error inesperado. Por favor, inténtalo de nuevo más tarde.';
            }

            app.innerHTML = `
                <div class="hero-section">
                    <div class="container">
                        <div class="row justify-content-center">
                            <div class="col-md-6 col-lg-5">
                                <div class="card login-card">
                                    <div class="card-body p-5 text-center">
                                        <svg class="logo mb-4" width="64" height="64" viewBox="0 0 100 100">
                                            <rect width="100" height="100" fill="none"/>
                                            <circle cx="50" cy="50" r="40" fill="none" stroke="#dc3545" stroke-width="8">
                                                <animate attributeName="stroke-dasharray" from="0,251.2" to="251.2,0" dur="1s" fill="freeze"/>
                                            </circle>
                                            <path d="M35 35 L65 65 M65 35 L35 65" stroke="#dc3545" stroke-width="8" fill="none">
                                                <animate attributeName="stroke-dasharray" from="0,90" to="90,0" dur="0.5s" fill="freeze" begin="0.6s"/>
                                            </path>
                                        </svg>
                                        <h3 class="text-light mb-4">Error de Verificación</h3>
                                        <p class="text-white mb-4">${errorMessage}</p>
                                        <a href="/profile" data-link class="btn btn-primary">
                                            <i class="fas fa-arrow-left me-2"></i>Volver a mi perfil
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
