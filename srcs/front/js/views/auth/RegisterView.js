import AuthService from '../../services/AuthService.js';
import { messages } from '../../translations.js';
import { getNavbarHTML } from '../../components/Navbar.js';

export async function RegisterView() {
    const app = document.getElementById('app');
    
    // Cargar templates
    const response = await fetch('/views/components/RegisterView.html');
    const html = await response.text();
    
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = html;
    
    // Agregar templates al documento
    const templates = tempDiv.querySelectorAll('template');
    templates.forEach(template => document.body.appendChild(template));

    app.innerHTML = getNavbarHTML(false);
    
    const mainTemplate = document.getElementById('mainRegisterTemplate');
    if (!mainTemplate) {
        console.error('Template principal no encontrado');
        return;
    }
    
    app.appendChild(mainTemplate.content.cloneNode(true));

    const gdprTemplate = document.getElementById('gdprModalTemplate');
    if (gdprTemplate) {
        app.appendChild(gdprTemplate.content.cloneNode(true));
    }
    setupEventListeners();
}

function setupEventListeners() {
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
                password: password,
                password2: password2,
                privacy_policy: privacyAccepted
            });

            app.innerHTML = `
                ${getNavbarHTML(false)}
                <div class="hero-section">
                    <div class="container">
                        <div class="row justify-content-center">
                            <div class="col-md-6 col-lg-5">
                                <div class="card login-card verification-message">
                                    <div class="card-body p-5 text-center">
                                        <svg class="logo mb-4" width="64" height="64" viewBox="0 0 100 100">
                                            <rect width="100" height="100" fill="none"/>
                                            <circle cx="50" cy="50" r="40" fill="none" stroke="#0d6efd" stroke-width="8">
                                                <!-- Animación de rotación infinita -->
                                                <animateTransform
                                                    attributeName="transform"
                                                    type="rotate"
                                                    from="0 50 50"
                                                    to="360 50 50"
                                                    dur="2s"
                                                    repeatCount="indefinite"/>
                                            </circle>
                                            <!-- Pulso en el centro -->
                                            <circle cx="50" cy="50" r="5" fill="#0d6efd">
                                                <animate
                                                    attributeName="r"
                                                    values="5;8;5"
                                                    dur="1s"
                                                    repeatCount="indefinite"/>
                                                <animate
                                                    attributeName="fill-opacity"
                                                    values="1;0.5;1"
                                                    dur="1s"
                                                    repeatCount="indefinite"/>
                                            </circle>
                                        </svg>
                                        <h3 class="text-light mb-3">${messages.AUTH.EMAIL_VERIFICATION.TITLE}</h3>
                                        <p class="text-white fs-6 mb-4">
                                            ${messages.AUTH.EMAIL_VERIFICATION.MESSAGE}<br>
                                            <small class="d-block mt-2 text-white-75">${messages.AUTH.EMAIL_VERIFICATION.SUBMESSAGE}</small>
                                        </p>
                                        <div class="d-grid">
                                            <a href="/login" class="btn btn-primary btn-lg">
                                                <i class="fas fa-arrow-left me-2"></i>${messages.AUTH.EMAIL_VERIFICATION.BUTTON}
                                            </a>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
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

    document.getElementById('showPrivacyPolicy').addEventListener('click', (e) => {
        e.preventDefault();
        const modal = new bootstrap.Modal(document.getElementById('gdprModal'));
        modal.show();
    });

    window.handleFtAuth = async () => {
        try {
            const authUrl = await AuthService.get42AuthUrl();
            window.location.href = authUrl;
        } catch (error) {
            const alertDiv = document.getElementById('registerAlert');
            alertDiv.innerHTML = `
                <div class="alert alert-danger">
                    <p>Error al iniciar sesión con 42: ${error.message}</p>
                </div>
            `;
        }
    };
}
