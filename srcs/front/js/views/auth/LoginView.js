import AuthService from '../../services/AuthService.js';
import { messages } from '../../translations.js';

export async function LoginView() {
    // Limpiar todo el estado al inicio
    await AuthService.clearSession();
    
    // Esperar un momento para asegurar que todo está limpio
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // Verificar si venimos de una verificación de email
    const isVerificationReturn = document.referrer.includes('/verify-email/');
    
    // Si no viene de verificación, asegurar que no hay estado guardado
    if (!isVerificationReturn) {
        localStorage.clear();
        sessionStorage.clear();
    }
    
    // Obtener el elemento app primero
    const app = document.getElementById('app');
    
    // Comprobar si hay código de 42 en la URL
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');

    if (code) {
        console.log('Código 42 detectado:', code);
        // Asegurar que el modal se crea antes de intentar mostrarlo
        app.innerHTML = `
            <div class="hero-section">
                <div class="container">
                    <div class="row justify-content-center">
                        <div class="col-md-6 col-lg-5">
                            <div class="card login-card">
                                <div class="card-body p-5 text-center">
                                    <div class="spinner-border text-primary mb-3"></div>
                                    <h4>Verificando autenticación...</h4>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Modal 2FA -->
            <div class="modal fade" id="twoFactorModal" data-bs-backdrop="static" tabindex="-1">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content bg-dark">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-shield-alt me-2"></i>
                                ${messages.AUTH.TWO_FACTOR.TITLE}
                            </h5>
                        </div>
                        <div class="modal-body">
                            <div class="status-message">
                                <i class="fas fa-envelope icon"></i>
                                <p class="mb-4">${messages.AUTH.TWO_FACTOR.MESSAGE}</p>
                            </div>
                            <div id="verify2FAAlert"></div>
                            <form id="verify2FAForm">
                                <div class="form-floating mb-3">
                                    <input type="text" class="form-control" 
                                           id="code" placeholder="Código" required
                                           pattern="[0-9]{6}" maxlength="6"
                                           autocomplete="off">
                                    <label for="code">Código de verificación</label>
                                </div>
                                <div class="d-grid">
                                    <button class="btn btn-primary btn-lg">
                                        <i class="fas fa-check me-2"></i>${messages.AUTH.TWO_FACTOR.BUTTON}
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        `;

        try {
            const result = await AuthService.handle42Callback(code);
            console.log('Resultado 42 callback:', result);
            
            if (result.status === 'pending_verification') {
                app.innerHTML = `
                    <div class="hero-section">
                        <div class="container">
                            <div class="row justify-content-center">
                                <div class="col-md-6 col-lg-5">
                                    <div class="card login-card verification-message">
                                        <div class="card-body p-5 text-center">
                                            <svg class="logo mb-4" width="64" height="64" viewBox="0 0 100 100">
                                                <rect width="100" height="100" fill="none"/>
                                                <circle cx="50" cy="50" r="40" fill="none" stroke="#0d6efd" stroke-width="8"/>
                                                <path d="M30 50 L45 65 L70 35" stroke="#0d6efd" stroke-width="8" fill="none"/>
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
                return;
            }
            
            if (result.status === 'pending_2fa') {
                // Asegurarnos de que el modal existe antes de inicializarlo
                const modalElement = document.getElementById('twoFactorModal');
                if (!modalElement) {
                    throw new Error('Error al inicializar el modal 2FA');
                }

                // Guardar datos en sessionStorage
                sessionStorage.setItem('pendingAuth', 'true');
                sessionStorage.setItem('fortytwo_user', 'true');
                sessionStorage.setItem('pendingUsername', result.username);

                // Inicializar y mostrar el modal
                const modal = new bootstrap.Modal(modalElement);
                modal.show();

                // Configurar el evento del formulario 2FA
                document.getElementById('verify2FAForm')?.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const code = document.getElementById('code').value;
                    const alertDiv = document.getElementById('verify2FAAlert');
                    
                    try {
                        const verifyResult = await AuthService.verify2FACode(code, true);
                        if (verifyResult.status === 'success') {
                            // Limpiar estado temporal
                            sessionStorage.removeItem('pendingAuth');
                            sessionStorage.removeItem('fortytwo_user');
                            sessionStorage.removeItem('pendingUsername');
                            
                            // Establecer autenticación
                            localStorage.setItem('isAuthenticated', 'true');
                            localStorage.setItem('username', verifyResult.username);
                            
                            // Ocultar modal y redirigir
                            modal.hide();
                            window.location.replace('/profile');
                        }
                    } catch (error) {
                        alertDiv.innerHTML = `
                            <div class="alert alert-danger">
                                <p>${error.message}</p>
                            </div>
                        `;
                    }
                });
            } else if (result.status === 'success') {
                localStorage.setItem('isAuthenticated', 'true');
                localStorage.setItem('username', result.username);
                window.location.replace('/profile');
            }
        } catch (error) {
            console.error('Error en 42 callback:', error);
            app.innerHTML = `
                <div class="hero-section">
                    <div class="container">
                        <div class="row justify-content-center">
                            <div class="col-md-6 col-lg-5">
                                <div class="card login-card verification-message">
                                    <div class="card-body p-5 text-center">
                                        <svg class="logo mb-4" width="64" height="64" viewBox="0 0 100 100">
                                            <rect width="100" height="100" fill="none"/>
                                            <circle cx="50" cy="50" r="40" fill="none" stroke="#0d6efd" stroke-width="8">
                                                <animate attributeName="stroke-dasharray" from="0,251.2" to="251.2,0" dur="2s" fill="freeze"/>
                                            </circle>
                                            <path d="M30 50 L45 65 L70 35" stroke="#0d6efd" stroke-width="8" fill="none">
                                                <animate attributeName="stroke-dasharray" from="0,90" to="90,0" dur="1s" fill="freeze" begin="1s"/>
                                            </path>
                                        </svg>
                                        <h3 class="text-light fw-bold mb-3">${messages.AUTH.EMAIL_VERIFICATION.TITLE}</h3>
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
        }
        return;
    }

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
                                    
                                    <button type="button" class="w-100 btn btn-lg btn-dark mb-3" 
                                            onclick="handleFtAuth()">
                                        <img src="/public/42_logo.png" alt="42 Logo" class="me-2" style="height: 40px;">
                                        Login
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

    // Añadir el modal de 2FA después del formulario de login
    app.innerHTML += `
        <div class="modal fade" id="twoFactorModal" data-bs-backdrop="static" tabindex="-1">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content bg-dark">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-shield-alt me-2"></i>
                            ${messages.AUTH.TWO_FACTOR.TITLE}
                        </h5>
                    </div>
                    <div class="modal-body">
                        <div class="status-message">
                            <i class="fas fa-envelope icon"></i>
                            <p class="mb-4">${messages.AUTH.TWO_FACTOR.MESSAGE}</p>
                        </div>
                        <div id="verify2FAAlert"></div>
                        <form id="verify2FAForm">
                            <div class="form-floating mb-3">
                                <input type="text" class="form-control" 
                                       id="code" placeholder="Código" required
                                       pattern="[0-9]{6}" maxlength="6"
                                       autocomplete="off">
                                <label for="code">Código de verificación</label>
                            </div>
                            <div class="d-grid">
                                <button class="btn btn-primary btn-lg">
                                    <i class="fas fa-check me-2"></i>${messages.AUTH.TWO_FACTOR.BUTTON}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>

        <!-- Modal de verificación completada -->
        <div class="modal fade" id="verificationSuccessModal">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content bg-dark">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-check-circle me-2"></i>
                            Verificación Completada
                        </h5>
                    </div>
                    <div class="modal-body text-center">
                        <div class="status-message">
                            <i class="fas fa-check-circle icon text-success"></i>
                            <p class="mb-4">Tu cuenta ha sido verificada correctamente.</p>
                        </div>
                        <div class="d-grid">
                            <button class="btn btn-primary btn-lg" data-bs-dismiss="modal">
                                <i class="fas fa-sign-in-alt me-2"></i>Continuar
                            </button>
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
            alertDiv.innerHTML = '';
            const result = await AuthService.login(username, password, remember);
            console.log('Resultado login:', result);
            
            if (result.status === 'success') {
                localStorage.setItem('isAuthenticated', 'true');
                localStorage.setItem('username', username);
                // Forzar recarga de la página al redirigir
                window.location.replace('/');
                return;
            }
            
            if (result.status === 'pending_2fa') {
                // Guardar estado temporal y mostrar modal 2FA
                sessionStorage.setItem('pendingAuth', 'true');
                sessionStorage.setItem('pendingUsername', username);
                const modal = new bootstrap.Modal(document.getElementById('twoFactorModal'));
                modal.show();
                // Limpiar y enfocar campo de código
                document.getElementById('code').value = '';
                document.getElementById('code').focus();
                return;
            }
            
            if (result.status === 'success') {
                localStorage.setItem('isAuthenticated', 'true');
                localStorage.setItem('username', username);
                window.location.replace('/profile');
            }
        } catch (error) {
            console.error('Error en login:', error);
            alertDiv.innerHTML = `
                <div class="alert alert-danger">
                    <p>${error.message}</p>
                </div>
            `;
        }
    });

    // Añadir manejador para el formulario 2FA
    document.getElementById('verify2FAForm')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const code = document.getElementById('code').value;
        const alertDiv = document.getElementById('verify2FAAlert');
        const isFortytwoUser = sessionStorage.getItem('fortytwo_user') === 'true';
        
        try {
            const result = await AuthService.verify2FACode(code, isFortytwoUser);
            if (result.status === 'success') {
                // Limpiar estado temporal
                sessionStorage.removeItem('pendingAuth');
                sessionStorage.removeItem('fortytwo_user');
                
                // Establecer autenticación
                localStorage.setItem('isAuthenticated', 'true');
                localStorage.setItem('username', result.username);
                
                // Ocultar modal y redirigir
                const modal = bootstrap.Modal.getInstance(document.getElementById('twoFactorModal'));
                modal.hide();
                window.location.replace('/profile');
            }
        } catch (error) {
            alertDiv.innerHTML = `
                <div class="alert alert-danger">
                    <p>${error.message}</p>
                </div>
            `;
        }
    });

    // Añadir esta función después de los event listeners existentes
    window.handleFtAuth = async () => {
        try {
            const authUrl = await AuthService.get42AuthUrl();
            window.location.href = authUrl;
        } catch (error) {
            const alertDiv = document.getElementById('loginAlert');
            alertDiv.innerHTML = `
                <div class="alert alert-danger">
                    <p>Error al iniciar sesión con 42: ${error.message}</p>
                </div>
            `;
        }
    };
}
