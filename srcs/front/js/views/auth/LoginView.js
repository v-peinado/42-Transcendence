import AuthService from '../../services/AuthService.js';

export async function LoginView() {
    // Verificar si el usuario ya está autenticado
    const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
    if (isAuthenticated) {
        // Reemplazar la entrada actual del historial con /profile
        window.history.replaceState(null, '', '/profile');
        // Redirigir al perfil
        window.location.href = '/profile';
        return;
    }

    // Limpiar cualquier estado anterior al cargar la vista de login
    if (!isAuthenticated) {
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
        // Mostrar pantalla de carga inmediatamente
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
        `;

        try {
            const result = await AuthService.handle42Callback(code);
            console.log('Resultado callback 42:', result);

            if (result.status === 'success') {
                localStorage.setItem('isAuthenticated', 'true');
                localStorage.setItem('username', result.username);
                window.location.href = '/profile';
                return;
            } else if (result.status === 'verified') {
                // Si el usuario ya está verificado, redirigir al perfil
                localStorage.setItem('isAuthenticated', 'true');
                localStorage.setItem('username', result.username);
                window.location.href = '/profile';
                return;
            } else if (result.needsEmailVerification) {
                // Solo mostrar mensaje de verificación si realmente necesita verificar
                app.innerHTML = `
                    <div class="hero-section">
                        <div class="container">
                            <div class="row justify-content-center">
                                <div class="col-md-6 col-lg-5">
                                    <div class="card login-card">
                                        <div class="card-body p-5">
                                            <div class="text-center mb-4">
                                                <h2 class="fw-bold">¡Cuenta Creada!</h2>
                                            </div>
                                            <div class="alert alert-success">
                                                <h5 class="mb-3">¡Gracias por registrarte!</h5>
                                                <p class="mb-0">Te hemos enviado un email con las instrucciones para activar tu cuenta.</p>
                                            </div>
                                            <div class="text-center mt-4">
                                                <a href="/login" data-link class="btn btn-primary">Volver al Login</a>
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
        } catch (error) {
            console.error('Error en callback de 42:', error);
            app.innerHTML = `
                <div class="hero-section">
                    <div class="container">
                        <div class="row justify-content-center">
                            <div class="col-md-6 col-lg-5">
                                <div class="card login-card">
                                    <div class="card-body p-5">
                                        <div class="alert alert-danger">
                                            <h4>Error de Autenticación</h4>
                                            <p>${error.message}</p>
                                            <div class="mt-3">
                                                <a href="/login" class="btn btn-primary">Volver a intentar</a>
                                            </div>
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
                // Reemplazar la entrada actual del historial
                window.history.replaceState(null, '', '/profile');
                window.location.href = '/profile';
            } else if (result.needsEmailVerification) {
                alertDiv.innerHTML = `
                    <div class="alert alert-warning">
                        <p>${result.message}</p>
                        <div class="mt-3">
                            <p>Por favor, revisa tu email para activar tu cuenta.</p>
                        </div>
                    </div>
                `;
            }
        } catch (error) {
            alertDiv.innerHTML = `
                <div class="alert alert-danger">
                    <p>${error.message}</p>
                </div>
            `;
            setTimeout(() => {
                alertDiv.innerHTML = '';
            }, 3000);
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
