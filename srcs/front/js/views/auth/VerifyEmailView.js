import AuthService from '../../services/AuthService.js';
import { getNavbarHTML } from '../../components/Navbar.js';
import { messages } from '../../translations.js';  // Añadir esta importación

export function VerifyEmailView(uidb64, token) {
    const app = document.getElementById('app');
    
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
                ${getNavbarHTML(false)}
                <div class="hero-section">
                    <div class="container">
                        <div class="row justify-content-center">
                            <div class="col-md-6 col-lg-5">
                                <div class="verification-message"> <!-- Quitar success-message -->
                                    <div class="card-body p-5 text-center">
                                        <svg class="logo mb-4" width="64" height="64" viewBox="0 0 100 100">
                                            <rect width="100" height="100" fill="none"/>
                                            <circle cx="50" cy="50" r="40" fill="none" stroke="#0d6efd" stroke-width="8">
                                                <animate attributeName="stroke-dasharray" 
                                                         from="0,251.2" 
                                                         to="251.2,0" 
                                                         dur="1s" 
                                                         fill="freeze"/>
                                            </circle>
                                            <path d="M30 50 L45 65 L70 35" 
                                                  stroke="#0d6efd" 
                                                  stroke-width="8" 
                                                  fill="none"
                                                  stroke-dasharray="0,90"
                                                  stroke-dashoffset="0">
                                                <animate attributeName="stroke-dasharray" 
                                                         from="0,90" 
                                                         to="90,0" 
                                                         dur="0.5s" 
                                                         fill="freeze"
                                                         begin="0.6s"/>
                                            </path>
                                        </svg>
                                        <h3 class="text-light mb-3">${messages.AUTH.EMAIL_VERIFICATION.SUCCESS_TITLE}</h3>
                                        <p class="text-white fs-6 mb-4">
                                            ${messages.AUTH.EMAIL_VERIFICATION.SUCCESS_MESSAGE}
                                        </p>
                                        <div class="d-grid">
                                            <a href="/login" class="btn btn-primary btn-lg">
                                                <i class="fas fa-sign-in-alt me-2"></i>${messages.AUTH.EMAIL_VERIFICATION.SUCCESS_BUTTON}
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
                                            <circle cx="50" cy="50" r="40" fill="none" stroke="#dc3545" stroke-width="8">
                                                <animate attributeName="stroke-dasharray" 
                                                         from="0,251.2" 
                                                         to="251.2,0" 
                                                         dur="1s" 
                                                         fill="freeze"/>
                                            </circle>
                                            <path d="M35 35 L65 65 M65 35 L35 65" 
                                                  stroke="#dc3545" 
                                                  stroke-width="8" 
                                                  fill="none"
                                                  stroke-dasharray="0,90"
                                                  stroke-dashoffset="0">
                                                <animate attributeName="stroke-dasharray" 
                                                         from="0,90" 
                                                         to="90,0" 
                                                         dur="0.5s" 
                                                         fill="freeze"
                                                         begin="0.6s"/>
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
