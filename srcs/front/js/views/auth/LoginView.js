import AuthService from '../../services/AuthService.js';
import { AuthUtils } from '../../services/auth/AuthUtils.js';
import { messages } from '../../translations.js';
import { getNavbarHTML } from '../../components/Navbar.js';
import RateLimitService from '../../services/RateLimitService.js';

export async function LoginView() {
    // Limpiar estado inicial
    await AuthService.clearSession();
    await new Promise(resolve => setTimeout(resolve, 100));
    
    const isVerificationReturn = document.referrer.includes('/verify-email/');
    if (!isVerificationReturn) {
        localStorage.clear();
        sessionStorage.clear();
    }

    // Obtener el elemento app
    const app = document.getElementById('app');
    
    // Cargar templates
    const response = await fetch('/views/components/LoginView.html');
    const html = await response.text();
    
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = html;
    
    // Agregar templates al documento
    const templates = tempDiv.querySelectorAll('template');
    templates.forEach(template => document.body.appendChild(template));

    // Comprobar código 42
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');

    if (code) {
        console.log('Código 42 detectado:', code);
        
        try {
            // Limpiar vista y mostrar loading
            app.innerHTML = getNavbarHTML(false);
            const loadingTemplate = document.getElementById('loading42Template');
            if (loadingTemplate) {
                app.appendChild(loadingTemplate.content.cloneNode(true));
            }

            const result = await AuthService.handle42Callback(code);
            console.log('Resultado 42 callback:', result);

            // Primero manejar 2FA si es necesario
            if (result.status === 'pending_2fa' || result.require_2fa) {
                // Obtener los templates necesarios primero
                const mainTemplate = document.getElementById('mainLoginTemplate');
                const twoFactorModalTemplate = document.getElementById('twoFactorModalTemplate');

                // Limpiar vista
                app.innerHTML = getNavbarHTML(false);

                if (result.status === 'pending_2fa' || result.require_2fa) {
                    if (mainTemplate && twoFactorModalTemplate) {
                        // Limpiar la URL del código 42
                        window.history.replaceState({}, '', '/login');
                        
                        // Mostrar vista base y modal
                        app.appendChild(mainTemplate.content.cloneNode(true));
                        app.appendChild(twoFactorModalTemplate.content.cloneNode(true));
                        
                        // Configurar estado
                        sessionStorage.setItem('pendingAuth', 'true');
                        sessionStorage.setItem('fortytwo_user', 'true');
                        sessionStorage.setItem('pendingUsername', result.username);

                        // IMPORTANTE: Configurar los event listeners antes de mostrar el modal
                        setupEventListeners();

                        // Mostrar modal
                        const modal = new bootstrap.Modal(document.getElementById('twoFactorModal'));
                        modal.show();

                        // Enfocar el input del código
                        document.getElementById('code').value = '';
                        document.getElementById('code').focus();
                    }
                    return;
                }
                return;
            }

            // Manejar verificación pendiente y mostrar GDPR
            if (result.status === 'pending_verification' || 
                (result.status === 'error' && result.message?.includes('verification'))) {
                
                // Mostrar GDPR primero si no lo ha aceptado
                const hasAcceptedGDPR = localStorage.getItem('42_gdpr_accepted');
                if (!hasAcceptedGDPR) {
                    const gdpr42ModalTemplate = document.getElementById('gdpr42ModalTemplate');
                    if (gdpr42ModalTemplate) {
                        app.appendChild(gdpr42ModalTemplate.content.cloneNode(true));
                        
                        const gdpr42ModalElement = document.getElementById('gdpr42Modal');
                        if (!gdpr42ModalElement) {
                            throw new Error('Modal GDPR no encontrado');
                        }
                        
                        const gdpr42Modal = new bootstrap.Modal(gdpr42ModalElement, {
                            backdrop: 'static',
                            keyboard: false
                        });
                        
                        // Esperar respuesta del usuario
                        await new Promise((resolve, reject) => {
                            const acceptBtn = document.getElementById('accept42GDPRBtn');
                            if (acceptBtn) {
                                acceptBtn.onclick = () => {
                                    localStorage.setItem('42_gdpr_accepted', 'true');
                                    gdpr42Modal.hide();
                                    resolve(true);
                                };
                            }
                            
                            gdpr42ModalElement.addEventListener('hidden.bs.modal', () => {
                                if (!localStorage.getItem('42_gdpr_accepted')) {
                                    reject('GDPR not accepted');
                                }
                            });
                            
                            gdpr42Modal.show();
                        });
                    }
                }

                // Después de GDPR, mostrar mensaje de verificación
                const verify42MessageTemplate = document.getElementById('verify42MessageTemplate');
                if (verify42MessageTemplate) {
                    app.innerHTML = getNavbarHTML(false);
                    app.appendChild(verify42MessageTemplate.content.cloneNode(true));
                }
                return;
            }

            // Resto del flujo para éxito o otros estados
            if (result.status === 'success') {
                localStorage.setItem('isAuthenticated', 'true');
                localStorage.setItem('username', result.username);
                
                // Reutilizar el loading42Template
                app.innerHTML = getNavbarHTML(false);
                const loadingTemplate = document.getElementById('loading42Template');
                if (loadingTemplate) {
                    const loadingScreen = loadingTemplate.content.cloneNode(true);
                    // Personalizar el mensaje
                    loadingScreen.querySelector('h4').textContent = 'Preparando tu experiencia de juego...';
                    app.appendChild(loadingScreen);
                }

                // Dar tiempo para que se muestre la pantalla de carga
                await new Promise(resolve => setTimeout(resolve, 800));
                
                // Precargar GameView mientras se muestra la carga
                await import('../game/GameView.js');
                
                window.location.replace('/game');
                return;
            }

        } catch (error) {
            console.error('Error en autenticación 42:', error);
            
            if (error === 'GDPR not accepted' || error.message === 'GDPR not accepted') {
                window.location.replace('/login');
                return;
            }

            if (error.message?.includes('invalid_grant')) {
                window.location.replace('/login');
                return;
            }

            const errorTemplate = document.getElementById('alertTemplate');
            if (errorTemplate) {
                const alert = errorTemplate.content.cloneNode(true);
                alert.querySelector('p').textContent = 'Error en la autenticación. Por favor, intente nuevamente.';
                app.appendChild(alert);
            }
        }
        return;
    }

    // Vista principal de login
    const mainTemplate = document.getElementById('mainLoginTemplate');
    if (!mainTemplate) {
        console.error('Template principal no encontrado');
        return;
    }

    // Renderizar vista principal
    app.innerHTML = getNavbarHTML(false);
    app.appendChild(mainTemplate.content.cloneNode(true));

    // Añadir modales necesarios
    const twoFactorModal = document.getElementById('twoFactorModalTemplate');
    const qrScannerModal = document.getElementById('qrScannerModalTemplate');
    if (twoFactorModal) app.appendChild(twoFactorModal.content.cloneNode(true));
    if (qrScannerModal) app.appendChild(qrScannerModal.content.cloneNode(true));

    // Configurar event listeners
    setupEventListeners();
}

function showError(message) {
    const alertDiv = document.getElementById('loginAlert');
    if (!alertDiv) return;
    
    const errorResult = AuthUtils.mapBackendError(message);
    alertDiv.innerHTML = errorResult.html;
}

// Mover todos los event listeners a una función separada
function setupEventListeners() {
    const form = document.getElementById('loginForm');
    const logo = document.getElementById('loginLogo');

    if (form && logo) {
        form.addEventListener('focusin', () => {
            logo.classList.add('animated');
        });

        form.addEventListener('focusout', (e) => {
            if (!form.contains(document.activeElement)) {
                logo.classList.remove('animated');
            }
        });

        form.addEventListener('submit', handleFormSubmit);
    }

    // Setup 2FA form listener
    const verify2FAForm = document.getElementById('verify2FAForm');
    if (verify2FAForm) {
        verify2FAForm.addEventListener('submit', handle2FASubmit);
    }

    // Setup QR scanner buttons
    const scanQRBtn = document.getElementById('scanQRBtn');
    if (scanQRBtn) {
        scanQRBtn.addEventListener('click', handleScanQRClick);
    }

    const scanQRWithCameraBtn = document.getElementById('scanQRWithCameraBtn');
    if (scanQRWithCameraBtn) {
        scanQRWithCameraBtn.addEventListener('click', handleScanQRWithCamera);
    }

    const uploadQRBtn = document.getElementById('uploadQRBtn');
    if (uploadQRBtn) {
        uploadQRBtn.addEventListener('click', () => {
            document.getElementById('qrFileInput')?.click();
        });
    }

    const qrFileInput = document.getElementById('qrFileInput');
    if (qrFileInput) {
        qrFileInput.addEventListener('change', handleQRFileUpload);
    }
}

// Mover las funciones de manejo de eventos aquí...
async function handleFormSubmit(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const remember = document.getElementById('remember').checked;
    const alertDiv = document.getElementById('loginAlert');
    const submitButton = e.target.querySelector('button[type="submit"]');
    
    alertDiv.innerHTML = '';
    
    try {
        const result = await AuthService.login(username, password, remember);
        
        if (result.status === 'success') {
            localStorage.setItem('isAuthenticated', 'true');
            localStorage.setItem('username', username);
            window.location.replace('/game');
            return;
        }

        if (result.status === 'rate_limit') {
            submitButton.disabled = true;
            alertDiv.innerHTML = `
                <div class="alert alert-warning fade show">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-exclamation-triangle fa-2x me-3"></i>
                        <div>
                            <h6 class="alert-heading mb-1">${result.title}</h6>
                            <span>${result.message}</span>
                        </div>
                    </div>
                </div>`;
            
            setTimeout(() => {
                submitButton.disabled = false;
                alertDiv.innerHTML = '';
            }, result.remaining_time * 1000);
            return;
        }

        // Añadir manejo de 2FA
        if (result.status === 'pending_2fa') {
            handlePending2FA(username);
            return;
        }

    } catch (error) {
        console.log('Form submit complete error:', error);
        
        // Si es un error de credenciales inválidas
        if (error.message === messages.AUTH.ERRORS.INVALID_CREDENTIALS) {
            alertDiv.innerHTML = AuthUtils.mapBackendError(messages.AUTH.ERRORS.INVALID_CREDENTIALS).html;
            return;
        }
        
        // Si el error viene como JSON string
        try {
            if (typeof error.message === 'string' && error.message.startsWith('{')) {
                const parsedError = JSON.parse(error.message);
                if (parsedError.status === 'error') {
                    if (parsedError.message === "['Incorrect username or password']") {
                        alertDiv.innerHTML = AuthUtils.mapBackendError(messages.AUTH.ERRORS.INVALID_CREDENTIALS).html;
                        return;
                    }
                }
            }
        } catch (e) {
            console.error('Error parsing error message:', e);
        }

        // Para cualquier otro tipo de error
        alertDiv.innerHTML = AuthUtils.mapBackendError(messages.AUTH.ERRORS.DEFAULT).html;
    }
}

// Actualiza handlePending2FA para asegurar que el modal existe
function handlePending2FA(username) {
    // Primero verificar si necesitamos añadir el template del modal
    if (!document.getElementById('twoFactorModal')) {
        const twoFactorModalTemplate = document.getElementById('twoFactorModalTemplate');
        if (twoFactorModalTemplate) {
            document.body.appendChild(twoFactorModalTemplate.content.cloneNode(true));
        }
    }

    sessionStorage.setItem('pendingAuth', 'true');
    sessionStorage.setItem('pendingUsername', username);
    
    const modal = new bootstrap.Modal(document.getElementById('twoFactorModal'));
    modal.show();
    
    const codeInput = document.getElementById('code');
    if (codeInput) {
        codeInput.value = '';
        codeInput.focus();
    }
}

async function handle2FASubmit(e) {
    e.preventDefault();
    const code = document.getElementById('code').value;
    const alertDiv = document.getElementById('verify2FAAlert');
    const submitButton = e.target.querySelector('button');
    const isFortytwoUser = sessionStorage.getItem('fortytwo_user') === 'true';
    const username = sessionStorage.getItem('pendingUsername');
    
    try {
        const result = await AuthService.verify2FACode(code, isFortytwoUser);
        
        if (result.status === 'rate_limit') {
            alertDiv.innerHTML = `
                <div class="alert alert-warning">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-lock fa-2x me-3"></i>
                        <div>
                            <h6 class="alert-heading mb-1">Usuario bloqueado</h6>
                            <span>Por razones de seguridad, tu cuenta ha sido bloqueada temporalmente. Podrás intentarlo de nuevo en ${RateLimitService.formatTimeRemaining(result.remaining_time)}.</span>
                        </div>
                    </div>
                </div>`;

            // Deshabilitar botón y limpiar código
            submitButton.disabled = true;
            document.getElementById('code').value = '';
            setTimeout(() => {
                submitButton.disabled = false;
                alertDiv.innerHTML = '';
            }, result.remaining_time * 1000);
            return;
        }

        if (result.status === 'error') {
            alertDiv.innerHTML = `
                <div class="alert alert-danger">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-exclamation-circle me-2"></i>
                        <strong>${result.title}</strong><br>
                        ${result.message}
                    </div>
                </div>`;
            document.getElementById('code').value = '';
            document.getElementById('code').focus();
            return;
        }

        if (result.status === 'success') {
            // Limpiar estado temporal solo después de una verificación exitosa
            sessionStorage.clear(); // Limpiar todo el sessionStorage
            
            // Asegurarse de establecer la autenticación
            localStorage.setItem('isAuthenticated', 'true');
            localStorage.setItem('username', result.username || username);
            localStorage.setItem('two_factor_enabled', 'true'); // Añadir esta línea
            
            // Ocultar modal y esperar a que se complete la transición
            const modalElement = document.getElementById('twoFactorModal');
            const modal = bootstrap.Modal.getInstance(modalElement);
            if (modal) {
                modal.hide();
                await new Promise(resolve => setTimeout(resolve, 500)); // Aumentar el tiempo de espera
            }

            // Redirigir después de que todo esté listo
            console.log('Redirigiendo a game después de 2FA exitoso');
            window.location.replace('/game');
            return;
        }
    } catch (error) {
        if (error.response?.status === 429 || 
            (error.message && error.message.includes('Too many attempts'))) {
            // Cerrar modal en caso de rate limit
            if (twoFactorModal) {
                twoFactorModal.hide();
            }
            
            const seconds = error.response?.data?.remaining_time || 900;
            const formattedTime = RateLimitService.formatTimeRemaining(seconds);
            
            mainAlertDiv.innerHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>${messages.AUTH.RATE_LIMIT.TITLE}</strong><br>
                    ${messages.AUTH.RATE_LIMIT.MESSAGES.two_factor.replace('{time}', formattedTime)}
                </div>`;

            const loginButton = document.querySelector('#loginForm button[type="submit"]');
            if (loginButton) {
                loginButton.disabled = true;
                setTimeout(() => {
                    loginButton.disabled = false;
                    mainAlertDiv.innerHTML = '';
                }, seconds * 1000);
            }
            return;
        }

        // Mantener el manejo de otros errores existente
        let errorMessage = error.response?.data?.message || error.message || 'Ha ocurrido un error en la verificación';
        alertDiv.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle me-2"></i>
                ${errorMessage}
            </div>
        `;
    }
}

function handleScanQRClick() {
    // Modificar la inicialización del modal
    const modalElement = document.getElementById('qrScannerModal');
    if (!modalElement) {
        console.error('Modal QR no encontrado');
        return;
    }
    const modal = new bootstrap.Modal(modalElement, {
        backdrop: 'static',
        keyboard: false
    });
    modal.show();
}

async function handleScanQRWithCamera() {
    const alertDiv = document.getElementById('qrScannerAlert');
    try {
        const container = document.getElementById('qrScannerContainer');
        const alertDiv = document.getElementById('qrScannerAlert');
        if (!container) {
            throw new Error('Contenedor del scanner no encontrado');
        }
        container.style.display = 'block';
        
        const video = document.getElementById('qrVideo');
        if (!video) {
            throw new Error('Elemento de video no encontrado');
        }

        const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: "environment" }
        });
        
        video.srcObject = stream;
        await video.play();

        function tick() {
            if (video.videoWidth) {
                const canvas = document.createElement('canvas');
                const canvasCtx = canvas.getContext('2d');
                canvas.height = video.videoHeight;
                canvas.width = video.videoWidth;
                canvasCtx.drawImage(video, 0, 0, canvas.width, canvas.height);
                
                const imageData = canvasCtx.getImageData(0, 0, canvas.width, canvas.height);
                const code = jsQR(imageData.data, imageData.width, imageData.height, {
                    inversionAttempts: "dontInvert",
                });

                if (code) {
                    // Detener el escaneo
                    stream.getTracks().forEach(track => track.stop());
                    
                    // Procesar el código QR sin cerrar el modal aquí
                    const username = code.data;
                    const modal = bootstrap.Modal.getInstance(document.getElementById('qrScannerModal'));
                    processQRCode(username, modal);
                    return;
                }
            }
            requestAnimationFrame(tick);
        }

        requestAnimationFrame(tick);

        // Cleanup cuando se cierre el modal
        const modalElement = document.getElementById('qrScannerModal');
        modalElement.addEventListener('hidden.bs.modal', () => {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
            container.style.display = 'none';
        });

    } catch (error) {
        console.error('Error en la cámara:', error);
        if (alertDiv) {
            alertDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    Error al acceder a la cámara: ${error.message}
                </div>`;
        }
    }
}

// Nueva función para procesar el código QR
async function processQRCode(username, modal) {
    const alertDiv = document.getElementById('qrScannerAlert');
    try {
        const result = await AuthService.validateQR(username);
        
        if (result.status === 'error') {
            if (alertDiv) {
                alertDiv.innerHTML = `
                    <div class="alert alert-${result.title === messages.AUTH.RATE_LIMIT.TITLE ? 'warning' : 'danger'}">
                        <div class="d-flex align-items-center">
                            <i class="fas fa-${result.title === messages.AUTH.RATE_LIMIT.TITLE ? 'exclamation-triangle' : 'exclamation-circle'} fa-2x me-3"></i>
                            <div>
                                <h6 class="alert-heading mb-1">${result.title}</h6>
                                <span>${result.message}</span>
                            </div>
                        </div>
                    </div>`;
            }
            return;
        }

        if (result.success) {
            // Solo cerramos el modal en caso de éxito
            modal.hide();
            
            if (result.require_2fa) {
                sessionStorage.setItem('pendingAuth', 'true');
                sessionStorage.setItem('pendingUsername', username);
                const twoFactorModal = new bootstrap.Modal(document.getElementById('twoFactorModal'));
                twoFactorModal.show();
            } else {
                localStorage.setItem('isAuthenticated', 'true');
                localStorage.setItem('username', username);
                window.location.replace('/game');
            }
        }
    } catch (error) {
        if (alertDiv) {
            alertDiv.innerHTML = `
                <div class="alert alert-danger">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-exclamation-circle fa-2x me-3"></i>
                        <div>
                            <h6 class="alert-heading mb-1">Error</h6>
                            <span>${error.message || 'Error al validar QR'}</span>
                        </div>
                    </div>
                </div>`;
        }
    }
}

async function handleQRFileUpload(e) {
    const file = e.target.files[0];
    const alertDiv = document.getElementById('qrScannerAlert');
    if (file) {
        try {
            const alertDiv = document.getElementById('qrScannerAlert');
            // Crear un canvas para procesar la imagen
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            const img = new Image();
            
            img.onload = async () => {
                canvas.width = img.width;
                canvas.height = img.height;
                ctx.drawImage(img, 0, 0);
                
                const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                const code = jsQR(imageData.data, imageData.width, imageData.height);
                
                if (code) {
                    const username = code.data;
                    const modal = bootstrap.Modal.getInstance(document.getElementById('qrScannerModal'));
                    modal.hide();
                    
                    try {
                        const result = await AuthService.validateQR(username);
                        console.log('Resultado validación QR:', result);
                        
                        if (result.status === 'rate_limit') {
                            if (alertDiv) {
                                alertDiv.innerHTML = `
                                    <div class="alert alert-warning">
                                        <i class="fas fa-exclamation-triangle me-2"></i>
                                        <strong>${result.title}</strong><br>
                                        ${result.message}
                                    </div>`;
                            }
                            return;
                        }
                        
                        if (result.status === 'error' && result.showInModal) {
                            if (alertDiv) {
                                alertDiv.innerHTML = `
                                    <div class="alert alert-danger">
                                        <i class="fas fa-exclamation-circle me-2"></i>
                                        ${result.message}
                                    </div>`;
                            }
                            return;
                        }

                        if (result.success) {
                            if (result.require_2fa) {
                                // Configurar y mostrar 2FA
                                sessionStorage.setItem('pendingAuth', 'true');
                                sessionStorage.setItem('pendingUsername', username);
                                const twoFactorModal = new bootstrap.Modal(document.getElementById('twoFactorModal'));
                                twoFactorModal.show();
                                document.getElementById('code').value = '';
                                document.getElementById('code').focus();
                            } else {
                                // Login directo
                                localStorage.setItem('isAuthenticated', 'true');
                                localStorage.setItem('username', username);
                                window.location.replace('/game');
                            }
                        } else {
                            throw new Error(result.error || 'Error validando el QR');
                        }
                    } catch (error) {
                        if (alertDiv) {
                            alertDiv.innerHTML = `
                                <div class="alert alert-danger">
                                    <i class="fas fa-exclamation-circle me-2"></i>
                                    ${error.message}
                                </div>`;
                        }
                    }
                } else {
                    if (alertDiv) {
                        alertDiv.innerHTML = `
                            <div class="alert alert-danger">
                                <i class="fas fa-exclamation-circle me-2"></i>
                                No se pudo detectar un código QR válido en la imagen
                            </div>`;
                    }
                }
            };
            
            img.src = URL.createObjectURL(file);
        } catch (error) {
            const alertDiv = document.getElementById('qrScannerAlert');
            if (alertDiv) {
                alertDiv.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-circle me-2"></i>
                        Error al procesar el archivo: ${error.message}
                    </div>`;
            }
        }
    }
}

// Añadir esta función después de los event listeners existentes
window.handleFtAuth = async () => {
    try {
        const authUrl = await AuthService.get42AuthUrl();
        window.location.href = authUrl;
    } catch (error) {
        const alertDiv = document.getElementById('loginAlert');
        showError('Error al iniciar sesión con 42: ' + error.message);
    }
};

// Añadir esta función auxiliar al principio del archivo
function createVerificationMessage() {
    const container = document.createElement('div');
    container.className = 'hero-section';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'container';
    
    const row = document.createElement('div');
    row.className = 'row justify-content-center';
    
    const col = document.createElement('div');
    col.className = 'col-md-6 col-lg-5';
    
    const card = document.createElement('div');
    card.className = 'card login-card verification-message';
    
    const cardBody = document.createElement('div');
    cardBody.className = 'card-body p-5 text-center';
    
    // Crear el SVG de animación
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('class', 'logo mb-4');
    svg.setAttribute('width', '64');
    svg.setAttribute('height', '64');
    svg.setAttribute('viewBox', '0 0 100 100');
    
    // Añadir los elementos del SVG...
    // (mantener el mismo SVG que usa RegisterView)
    
    const title = document.createElement('h3');
    title.className = 'text-light mb-3';
    title.textContent = messages.AUTH.EMAIL_VERIFICATION.TITLE;
    
    const message = document.createElement('p');
    message.className = 'text-white fs-6 mb-4';
    message.textContent = messages.AUTH.EMAIL_VERIFICATION.MESSAGE;
    
    const submessage = document.createElement('small');
    submessage.className = 'd-block mt-2 text-white-75';
    submessage.textContent = messages.AUTH.EMAIL_VERIFICATION.SUBMESSAGE;
    
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'd-grid';
    
    const button = document.createElement('a');
    button.href = '/login';
    button.className = 'btn btn-primary btn-lg';
    
    const icon = document.createElement('i');
    icon.className = 'fas fa-arrow-left me-2';
    
    button.appendChild(icon);
    button.appendChild(document.createTextNode(messages.AUTH.EMAIL_VERIFICATION.BUTTON));
    
    // Ensamblar todo
    message.appendChild(document.createElement('br'));
    message.appendChild(submessage);
    buttonContainer.appendChild(button);
    cardBody.append(svg, title, message, buttonContainer);
    card.appendChild(cardBody);    col.appendChild(card);    row.appendChild(col);    contentDiv.appendChild(row);    container.appendChild(contentDiv);        return container;
}