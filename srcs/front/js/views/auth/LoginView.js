import AuthService from '../../services/AuthService.js';
import { AuthUtils } from '../../services/auth/AuthUtils.js';
import { messages } from '../../translations.js';
import { getNavbarHTML } from '../../components/Navbar.js';

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
        
        // Limpiar vista y mostrar loading
        app.innerHTML = getNavbarHTML(false);
        const loadingTemplate = document.getElementById('loading42Template');
        if (loadingTemplate) {
            app.appendChild(loadingTemplate.content.cloneNode(true));
        }

        try {
            const result = await AuthService.handle42Callback(code);
            console.log('Resultado 42 callback:', result);

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

            if (result.status === 'pending_verification' || 
                (result.status === 'error' && result.message?.includes('verification'))) {
                const verify42MessageTemplate = document.getElementById('verify42MessageTemplate');
                if (verify42MessageTemplate) {
                    app.appendChild(verify42MessageTemplate.content.cloneNode(true));
                }
                return;
            }

            if (result.status === 'success') {
                localStorage.setItem('isAuthenticated', 'true');
                localStorage.setItem('username', result.username);
                window.location.replace('/'); // Cambiado de '/profile' a '/'
                return;
            }

        } catch (error) {
            console.error('Error en autenticación 42:', error);
            
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

function handleSuccessfulLogin(username) {
    localStorage.setItem('isAuthenticated', 'true');
    localStorage.setItem('username', username);
    window.location.replace('/profile');
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
    
    try {
        alertDiv.innerHTML = '';
        
        const result = await AuthService.login(username, password, remember);
        
        if (result.status === 'success') {
            localStorage.setItem('isAuthenticated', 'true');
            localStorage.setItem('username', result.username || username);
            window.location.replace('/'); // Cambiado de '/profile' a '/'
            return;
        }
        
        if (result.status === 'pending_2fa') {
            sessionStorage.setItem('pendingAuth', 'true');
            sessionStorage.setItem('pendingUsername', username);
            const modal = new bootstrap.Modal(document.getElementById('twoFactorModal'));
            modal.show();
            document.getElementById('code').value = '';
            document.getElementById('code').focus();
            return;
        }

        showError('Ha ocurrido un error inesperado');
    } catch (error) {
        console.error('Error en login:', error);
        showError(error.message || 'Ha ocurrido un error inesperado');
    }
}

function handlePending2FA(username) {
    sessionStorage.setItem('pendingAuth', 'true');
    sessionStorage.setItem('pendingUsername', username);
    const modal = new bootstrap.Modal(document.getElementById('twoFactorModal'));
    modal.show();
    document.getElementById('code').value = '';
    document.getElementById('code').focus();
}

async function handle2FASubmit(e) {
    e.preventDefault();
    const code = document.getElementById('code').value;
    const alertDiv = document.getElementById('verify2FAAlert');
    const isFortytwoUser = sessionStorage.getItem('fortytwo_user') === 'true';
    const username = sessionStorage.getItem('pendingUsername');
    
    try {
        // Añadir logs para debugging
        console.log('Enviando verificación 2FA:', { code, isFortytwoUser, username });
        
        const result = await AuthService.verify2FACode(code, isFortytwoUser);
        console.log('Resultado verificación 2FA:', result);
        
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
            console.log('Redirigiendo a profile después de 2FA exitoso');
            window.location.replace('/'); // Cambiado de '/profile' a '/'
            return;
        }

        // Si llegamos aquí, hubo un error
        throw new Error(result.message || 'Error en la verificación');
    } catch (error) {
        console.error('Error en verificación 2FA:', error);
        alertDiv.innerHTML = `
            <div class="alert alert-danger">
                ${error.message || 'Error en la verificación del código'}
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
    try {
        const container = document.getElementById('qrScannerContainer');
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
                    
                    // Ocultar el modal del scanner
                    const modal = bootstrap.Modal.getInstance(document.getElementById('qrScannerModal'));
                    modal.hide();
                    
                    // Procesar el código QR
                    const username = code.data;
                    AuthService.validateQR(username)
                        .then(result => {
                            if (result.success) {
                                if (result.require_2fa) {
                                    sessionStorage.setItem('pendingAuth', 'true');
                                    sessionStorage.setItem('pendingUsername', username);
                                    const twoFactorModal = new bootstrap.Modal(document.getElementById('twoFactorModal'));
                                    twoFactorModal.show();
                                } else {
                                    localStorage.setItem('isAuthenticated', 'true');
                                    localStorage.setItem('username', username);
                                    window.location.replace('/'); // Cambiado de '/profile' a '/'
                                }
                            } else {
                                throw new Error(result.error || 'Error validando el QR');
                            }
                        })
                        .catch(error => {
                            alert('Error al validar el QR: ' + error.message);
                        });
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
        alert('Error al acceder a la cámara: ' + error.message);
    }
}

async function handleQRFileUpload(e) {
    const file = e.target.files[0];
    if (file) {
        try {
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
                                window.location.replace('/'); // Cambiado de '/profile' a '/'
                            }
                        } else {
                            throw new Error(result.error || 'Error validando el QR');
                        }
                    } catch (error) {
                        console.error('Error en validación QR:', error);
                        alert('Error al validar el QR: ' + error.message);
                    }
                } else {
                    alert('No se pudo detectar un código QR válido en la imagen');
                }
            };
            
            img.src = URL.createObjectURL(file);
        } catch (error) {
            alert('Error al procesar el archivo: ' + error.message);
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