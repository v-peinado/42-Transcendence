import AuthService from '../../services/AuthService.js';
import { Auth2FA } from '../../services/auth/Auth2FA.js';
import { AuthGDPR } from '../../services/auth/AuthGDPR.js';
import { getNavbarHTML } from '../../components/Navbar.js';
import { loadHTML } from '../../utils/htmlLoader.js';  // Añadir esta importación

export async function UserProfileView() {
    document.body.setAttribute('data-page', 'profile');
    const app = document.getElementById('app');
    
    try {
        const [userInfo, twoFactorStatus, viewHtml, footerHtml] = await Promise.all([
            AuthService.getUserProfile(),
            Auth2FA.get2FAStatus(),
            loadHTML('/views/user/UserProfile.html'),
            loadHTML('/views/components/Footer.html')
        ]);

        const navbar = await getNavbarHTML(true, userInfo, true);

        // Renderizar vista base con footer
        app.innerHTML = navbar + viewHtml + footerHtml;
        
        // Renderizar información del usuario
        await renderUserInfo(userInfo);
        
        // Configurar 2FA
        setupTwoFactorAuth(twoFactorStatus);
        
        // Inicializar funcionalidades
        initializeTabs();
        setupProfileEvents();
        updateFormFields(userInfo);

    } catch (error) {
        console.error('Error loading profile view:', error);
        showError(app, error);
    }
}

function renderBaseView(app, navbar, viewHtml) {
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = navbar + viewHtml;
    app.innerHTML = '';
    while (tempDiv.firstChild) app.appendChild(tempDiv.firstChild);
}

async function renderUserInfo(userInfo) {
    const userInfoContainer = document.getElementById('userInfo');
    if (!userInfoContainer) return;

    const spinner = userInfoContainer.querySelector('#loadingSpinner');
    if (spinner) spinner.remove();

    // Crear elementos UI
    const container = createProfileContainer(userInfo);
    userInfoContainer.appendChild(container);
}

function createProfileContainer(userInfo) {
    const container = document.createElement('div');
    container.className = 'text-center';

    // Avatar container
    const avatarContainer = document.createElement('div');
    avatarContainer.className = 'position-relative mb-4 avatar-container';

    const img = document.createElement('img');
    img.id = 'profileImage';
    img.className = 'profile-avatar rounded-circle';
    img.alt = 'Profile';
    // Si hay profile_image personalizada, usarla sin importar si es usuario de 42
    img.src = userInfo.profile_image || 
              (userInfo.is_fortytwo_user ? userInfo.fortytwo_image : 
              `https://api.dicebear.com/7.x/avataaars/svg?seed=${userInfo.username}`);

    const buttonsContainer = document.createElement('div');
    buttonsContainer.className = 'avatar-buttons';

    // Botones
    const changeBtn = document.createElement('button');
    changeBtn.id = 'changeImageBtn';
    changeBtn.className = 'btn btn-sm btn-primary rounded-circle';
    changeBtn.innerHTML = '<i class="fas fa-camera"></i>';

    const restoreBtn = document.createElement('button');
    restoreBtn.id = 'restoreImageBtn';
    restoreBtn.className = 'btn btn-sm btn-outline-light rounded-circle';
    restoreBtn.innerHTML = '<i class="fas fa-undo"></i>';

    // Username y email
    const username = document.createElement('h3');
    username.id = 'profileUsername';
    username.className = 'mb-2';
    username.textContent = userInfo.username;

    const email = document.createElement('p');
    email.id = 'profileEmail';
    email.className = 'text-muted mb-3';
    email.textContent = userInfo.email;

    // Status badge
    const statusContainer = document.createElement('div');
    statusContainer.id = 'profileStatus';
    statusContainer.className = 'status-badge mb-4';

    const badge = document.createElement('span');
    badge.className = `badge ${userInfo.is_active ? 'bg-success' : 'bg-warning'}`;
    badge.textContent = userInfo.is_active ? 'Activo' : 'Pendiente';

    // Construir la estructura
    buttonsContainer.appendChild(changeBtn);
    buttonsContainer.appendChild(restoreBtn);
    avatarContainer.appendChild(img);
    avatarContainer.appendChild(buttonsContainer);
    statusContainer.appendChild(badge);

    container.appendChild(avatarContainer);
    container.appendChild(username);
    container.appendChild(email);
    container.appendChild(statusContainer);

    return container;
}

function setupTwoFactorAuth(twoFactorStatus) {
    const toggle2FABtn = document.getElementById('toggle2FABtn');
    const buttonText = document.getElementById('2faButtonText');
    if (!toggle2FABtn || !buttonText) return;

    toggle2FABtn.dataset.enabled = twoFactorStatus.toString();
    buttonText.textContent = twoFactorStatus ? 'Desactivar 2FA' : 'Activar 2FA';
    toggle2FABtn.classList.remove('btn-outline-info', 'btn-outline-warning');
    toggle2FABtn.classList.add(twoFactorStatus ? 'btn-outline-warning' : 'btn-outline-info');
}

function showError(container, error) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'alert alert-danger m-3';
    errorDiv.textContent = `Error cargando el perfil: ${error.message}`;
    container.appendChild(errorDiv);
}

function initializeTabs() {
    const tabs = document.querySelectorAll('.nav-link[data-bs-toggle="tab"]');
    
    tabs.forEach(tab => {
        const targetId = tab.getAttribute('data-bs-target');
        
        tab.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Remover clases active de todos los tabs y panes
            document.querySelectorAll('.nav-link').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(p => {
                p.classList.remove('active', 'show');
                p.style.display = 'none';
            });
            
            // Activar el tab actual
            tab.classList.add('active');
            
            // Activar el panel correspondiente
            const targetPane = document.querySelector(targetId);
            if (targetPane) {
                targetPane.classList.add('active', 'show');
                targetPane.style.display = 'block';
            }
        });
    });

    const firstTab = tabs[0];
    if (firstTab) {
        firstTab.click();
    }
}

function showErrorMessage(container, error) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger m-3';
    alertDiv.textContent = `Error cargando el perfil: ${error.message}`;
    container.appendChild(alertDiv);
}

function setupProfileEvents() {
    document.getElementById('saveProfileBtn')?.addEventListener('click', async () => {
        try {
            const userInfo = await AuthService.getUserProfile();
            
            // Bloquear cualquier intento de cambio para usuarios de 42
            if (userInfo.username.startsWith('42_')) {
                throw new Error('Los usuarios de 42 no pueden modificar su email');
            }

            const updates = {};
            const messageDiv = document.getElementById('editProfileMessage');
            
            // Verificación para usuarios de 42
            if (userInfo.fortytwo_id) {
                // Simplemente ignorar cualquier intento de cambio de email
                // y continuar con otros cambios si los hay
            } else {
                // Procesar cambios de email para usuarios normales
                const newEmail = document.getElementById('editEmail').value;
                const currentEmail = document.getElementById('profileEmail').textContent;
                if (newEmail !== currentEmail) {
                    updates.email = newEmail;
                }
            }

            // Verificar cambios de contraseña
            const currentPassword = document.getElementById('currentPassword').value;
            const newPassword1 = document.getElementById('newPassword1').value;
            const newPassword2 = document.getElementById('newPassword2').value;

            if (newPassword1 || newPassword2 || currentPassword) {
                if (!currentPassword) {
                    throw new Error('Debes introducir tu contraseña actual');
                }
                if (newPassword1 !== newPassword2) {
                    throw new Error('Las contraseñas nuevas no coinciden');
                }
                updates.current_password = currentPassword;
                updates.new_password1 = newPassword1;
                updates.new_password2 = newPassword2;
            }

            if (Object.keys(updates).length === 0) {
                alert('No has realizado ningún cambio.');
                return;
            }

            const result = await AuthService.updateProfile(updates);
            
            if (result.status === 'rate_limit') {
                messageDiv.classList.remove('d-none', 'alert-success');
                messageDiv.classList.add('alert-warning');
                messageDiv.innerHTML = `
                    <div class="d-flex align-items-center">
                        <i class="fas fa-exclamation-triangle fa-2x me-3"></i>
                        <div>
                            <h6 class="alert-heading mb-1">${result.title}</h6>
                            <span>${result.message}</span>
                        </div>
                    </div>`;
                return;
            }

            // Si hay cambio de email, mostrar siempre el mensaje de verificación
            if (updates.email) {
                messageDiv.classList.remove('d-none', 'alert-danger');
                messageDiv.classList.add('alert-success');
                messageDiv.innerHTML = `
                    <i class="fas fa-info-circle me-2"></i>
                    Se ha enviado un email de verificación a ${updates.email}. 
                    Por favor, revisa tu bandeja de entrada.
                `;
            } else if (updates.current_password) {
                // Mostrar mensaje de contraseña actualizada
                messageDiv.classList.remove('d-none', 'alert-danger');
                messageDiv.classList.add('alert-success');
                messageDiv.innerHTML = `
                    <i class="fas fa-check-circle me-2"></i>
                    ${result.message || 'Tu contraseña ha sido actualizada correctamente'}
                `;
                
                // Limpiar campos de contraseña
                document.getElementById('currentPassword').value = '';
                document.getElementById('newPassword1').value = '';
                document.getElementById('newPassword2').value = '';
            }

            // Ocultar el mensaje después de 5 segundos
            setTimeout(() => {
                messageDiv.classList.add('d-none');
            }, 5000);

        } catch (error) {
            const messageDiv = document.getElementById('editProfileMessage');
            messageDiv.classList.remove('d-none', 'alert-success');
            messageDiv.classList.add('alert-danger');
            messageDiv.innerHTML = `
                <i class="fas fa-exclamation-circle me-2"></i>
                ${error.message || 'Error al actualizar el perfil'}
            `;
        }
    });

    document.getElementById('deleteAccountBtn')?.addEventListener('click', async () => {
        try {
            const userInfo = await AuthService.getUserProfile();
            
            const template = document.getElementById('profileModals');
            if (!template) {
                throw new Error('Template de modales no encontrado');
            }

            let modalElement = document.getElementById('deleteAccountModal');
            if (!modalElement) {
                const modalContent = template.content.cloneNode(true);
                document.body.appendChild(modalContent);
                modalElement = document.getElementById('deleteAccountModal');

                // 4. Si es usuario de 42, ocultar el campo de contraseña
                if (userInfo.is_fortytwo_user) {
                    const passwordGroup = modalElement.querySelector('.form-group');
                    if (passwordGroup) {
                        passwordGroup.style.display = 'none';
                    }
                }

                // 5. Añadir event listener al botón de confirmar
                document.getElementById('confirmDeleteBtn')?.addEventListener('click', async () => {
                    try {
                        const button = document.getElementById('confirmDeleteBtn');
                        button.disabled = true;
                        button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Eliminando...';

                        const password = userInfo.is_fortytwo_user ? null : 
                                       document.getElementById('deleteAccountPassword')?.value;
                        
                        if (!userInfo.is_fortytwo_user && !password) {
                            throw new Error('Debes introducir tu contraseña para eliminar tu cuenta');
                        }

                        const result = await AuthGDPR.deleteAccount(password);

                        if (result.status === 'success') {
                            showAlert('Tu cuenta será eliminada correctamente', 'success');
                            setTimeout(() => {
                                localStorage.clear();
                                sessionStorage.clear();
                                window.location.href = '/';
                            }, 1500);
                        } else {
                            throw new Error(result.message || 'Error al eliminar la cuenta');
                        }
                    } catch (error) {
                        console.error('Error al eliminar cuenta:', error);
                        showAlert(error.message, 'danger');
                        
                        // Restaurar el botón
                        const button = document.getElementById('confirmDeleteBtn');
                        button.disabled = false;
                        button.innerHTML = '<i class="fas fa-trash-alt me-2"></i>Eliminar Cuenta';
                    }
                });
            }

            // 6. Mostrar el modal
            const modal = new bootstrap.Modal(modalElement);
            modal.show();

        } catch (error) {
            console.error('Error al mostrar el modal:', error);
            showAlert('Error al mostrar el modal de eliminación', 'danger');
        }
    });

    // Añade estos event listeners después de renderizar el template
    document.getElementById('changeImageBtn')?.addEventListener('click', () => {
        document.getElementById('imageInput').click();
    });

    document.getElementById('imageInput')?.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        const alertEl = document.getElementById('imageAlert');
        const input = e.target;
        
        if (file) {
            try {
                // Validar tamaño y tipo
                if (file.size > 5 * 1024 * 1024) {
                    alertEl.className = 'alert alert-danger';
                    alertEl.textContent = 'La imagen no debe superar 2MB';
                    alertEl.style.display = 'block';
                    return;
                }

                // Validar formato
                const allowedFormats = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
                if (!allowedFormats.includes(file.type)) {
                    alertEl.className = 'alert alert-danger';
                    alertEl.textContent = 'Formato no válido. Se permiten: JPG, PNG, GIF y WEBP';
                    alertEl.style.display = 'block';
                    return;
                }

                const userInfo = await AuthService.updateProfileImage(file);
                
                if (userInfo && userInfo.profile_image) {
                    // Actualizar todas las instancias de la imagen
                    const imageUrl = userInfo.profile_image;
                    const imageElements = document.querySelectorAll('#profileImage, #navbarUserAvatar, #dropdownUserAvatar');
                    imageElements.forEach(el => {
                        if (el) el.src = imageUrl;
                    });

                    alertEl.className = 'alert alert-success';
                    alertEl.textContent = 'Imagen actualizada correctamente';
                } else {
                    throw new Error('Error al actualizar la imagen');
                }
            } catch (error) {
                alertEl.className = 'alert alert-danger';
                // Manejar específicamente el error de formato WebP
                if (error.message.includes('<html>')) {
                    alertEl.textContent = 'El formato WebP no está soportado. Por favor, usa JPG, PNG o GIF.';
                } else {
                    alertEl.textContent = error.message || 'Error al actualizar la imagen';
                }
            } finally {
                input.value = '';
                alertEl.style.display = 'block';
            }
        }
    });

    document.getElementById('restoreImageBtn')?.addEventListener('click', async () => {
        const alertEl = document.getElementById('imageAlert');
        const imageInput = document.getElementById('imageInput');
        
        try {
            // Esperamos la respuesta del backend con la imagen restaurada
            const response = await AuthService.updateProfile({ restore_image: true });
            
            // Obtenemos la información actualizada del usuario después de restaurar
            const userInfo = await AuthService.getUserProfile();
            
            // Para usuarios de 42, usamos siempre fortytwo_image si existe
            const imageUrl = userInfo.is_fortytwo_user ? 
                userInfo.fortytwo_image : 
                (userInfo.profile_image || `https://api.dicebear.com/7.x/avataaars/svg?seed=${userInfo.username}`);

            // Actualizamos todas las instancias de la imagen
            const imageElements = document.querySelectorAll('#profileImage, #navbarUserAvatar, #dropdownUserAvatar');
            imageElements.forEach(el => {
                if (el) {
                    el.src = imageUrl;
                }
            });

            alertEl.className = 'alert alert-success';
            alertEl.textContent = 'Imagen restaurada correctamente';
            
            if (imageInput) imageInput.value = '';
            
        } catch (error) {
            alertEl.className = 'alert alert-danger';
            alertEl.textContent = error.message;
        }
        alertEl.style.display = 'block';
    });

    // Actualizar el event listener para el botón de 2FA
    document.getElementById('toggle2FABtn')?.addEventListener('click', async () => {
        try {
            const button = document.getElementById('toggle2FABtn');
            const is2FAEnabled = button.dataset.enabled === 'true';

            if (!is2FAEnabled) {
                // Obtener y clonar el template
                const template = document.getElementById('modal2FATemplate');
                const modalElement = template.content.cloneNode(true);
                document.body.appendChild(modalElement);

                // Inicializar y mostrar el modal
                const modal = new bootstrap.Modal(document.getElementById('confirm2FAModal'));
                modal.show();

                // Configurar el event listener para el botón de confirmación
                document.getElementById('confirm2FABtn').addEventListener('click', async () => {
                    try {
                        const result = await Auth2FA.enable2FA();
                        if (result.success) {
                            button.dataset.enabled = 'true';
                            document.getElementById('2faButtonText').textContent = 'Desactivar 2FA';
                            button.classList.replace('btn-outline-info', 'btn-outline-warning');
                            modal.hide();
                            showAlert('2FA activado correctamente', 'success');
                        }
                    } catch (error) {
                        showAlert(error.message, 'danger');
                    }
                });

                // Limpiar el modal cuando se cierre
                document.getElementById('confirm2FAModal').addEventListener('hidden.bs.modal', function () {
                    this.remove();
                });
            } else {
                // Obtener y clonar el template de desactivación
                const template = document.getElementById('modalDisable2FATemplate');
                const modalElement = template.content.cloneNode(true);
                document.body.appendChild(modalElement);

                // Inicializar y mostrar el modal
                const modal = new bootstrap.Modal(document.getElementById('disable2FAModal'));
                modal.show();

                // Configurar el checkbox
                const checkbox = document.getElementById('confirm2FADisable');
                const confirmBtn = document.getElementById('confirm2FADisableBtn');
                checkbox.addEventListener('change', (e) => {
                    confirmBtn.disabled = !e.target.checked;
                });

                // Configurar el botón de confirmación
                confirmBtn.addEventListener('click', async () => {
                    try {
                        const result = await Auth2FA.disable2FA();
                        if (result.success) {
                            button.dataset.enabled = 'false';
                            document.getElementById('2faButtonText').textContent = 'Activar 2FA';
                            button.classList.replace('btn-outline-warning', 'btn-outline-info');
                            modal.hide();
                            showAlert('2FA desactivado correctamente', 'success');
                        }
                    } catch (error) {
                        showAlert(error.message, 'danger');
                    }
                });

                // Limpiar el modal cuando se cierre
                document.getElementById('disable2FAModal').addEventListener('hidden.bs.modal', function () {
                    this.remove();
                });
            }
        } catch (error) {
            showAlert(error.message, 'danger');
        }
    });

    // Añadir el event listener para el botón QR
    document.getElementById('showQRBtn')?.addEventListener('click', async () => {
        try {
            const template = document.getElementById('qrModalTemplate');
            if (!template) throw new Error('Template QR no encontrado');
            
            // Clonar y añadir el modal al DOM
            const modalElement = template.content.cloneNode(true);
            document.body.appendChild(modalElement);
            
            // Inicializar y mostrar el modal
            const modal = new bootstrap.Modal(document.getElementById('qrModal'));
            const qrContainer = document.getElementById('qrContainer');
            qrContainer.innerHTML = '<div class="spinner-border text-primary"></div>';
            modal.show();
            
            const username = localStorage.getItem('username');
            try {
                const qrUrl = await Auth2FA.generateQR(username);
                const qrImage = new Image();
                qrImage.src = qrUrl;
                qrImage.alt = 'QR Code';
                qrImage.className = 'img-fluid';
                qrImage.style.maxWidth = '256px';
                
                qrImage.onload = () => {
                    qrContainer.innerHTML = '';
                    qrContainer.appendChild(qrImage);
                    
                    const downloadBtn = document.getElementById('downloadQRBtn');
                    if (downloadBtn) {
                        downloadBtn.addEventListener('click', () => {
                            const canvas = document.createElement('canvas');
                            canvas.width = qrImage.naturalWidth;
                            canvas.height = qrImage.naturalHeight;
                            const ctx = canvas.getContext('2d');
                            ctx.drawImage(qrImage, 0, 0);
                            
                            const link = document.createElement('a');
                            link.download = `qr-login-${username}.png`;
                            link.href = canvas.toDataURL('image/png');
                            link.click();
                        });
                    }
                };

                qrImage.onerror = (error) => {
                    console.error('Error al cargar la imagen QR:', error);
                };

            } catch (error) {
                console.error('Error generando QR:', error);
                if (error.message?.includes('Demasiados intentos')) {
                    showAlert(error.message, 'warning');
                    modal.hide();
                    // Limpiar el modal del DOM
                    setTimeout(() => {
                        document.getElementById('qrModal')?.remove();
                    }, 500);
                } else {
                    qrContainer.innerHTML = `
                        <div class="alert alert-danger">
                            <i class="fas fa-exclamation-circle me-2"></i>
                            <div>
                                <strong>Error al generar el código QR</strong><br>
                                ${error.message}
                            </div>
                        </div>`;
                }
            }
        } catch (error) {
            showAlert('No se pudo generar el código QR: ' + error.message, 'danger');
        }
    });

    // Eliminar el event listener anterior del botón GDPR
    // Añadir los nuevos event listeners para GDPR
    document.getElementById('downloadDataBtn')?.addEventListener('click', handleDataDownload);
    document.getElementById('requestDataDeletionBtn')?.addEventListener('click', handleDataDeletion);

    // Actualizar el event listener del botón de logout
    document.getElementById('navLogoutBtn')?.addEventListener('click', handleLogout);
    document.getElementById('logoutBtn')?.addEventListener('click', handleLogout);

    // Agregar la función handleLogout
    async function handleLogout() {
        try {
            await AuthService.logout();
            localStorage.removeItem('isAuthenticated');
            localStorage.removeItem('username');
            window.location.replace('/');
        } catch (error) {
            console.error('Error en logout:', error);
            // Intentar cerrar sesión de todas formas
            localStorage.clear();
            sessionStorage.clear();
            window.location.replace('/');
        }
    }

    // Agregar limpieza del modal cuando se cierre
    document.body.addEventListener('hidden.bs.modal', function(event) {
        if (event.target.id === 'qrModal') {
            event.target.remove();
        }
    });
}

// Función auxiliar para mostrar alertas
function showAlert(message, type) {
    const template = document.getElementById('alertTemplate');
    if (!template) {
        console.error('Template de alerta no encontrado');
        return;
    }
    
    const element = template.content.cloneNode(true);
    const alertEl = element.querySelector('.alert');
    
    alertEl.className = `alert alert-${type} fade show`;
    alertEl.querySelector('i').className = 
        `fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}`;
    alertEl.querySelector('p').textContent = message;
    
    // Buscar el contenedor de alertas o crear uno nuevo
    let alertContainer = document.getElementById('alertContainer');
    if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.id = 'alertContainer';
        alertContainer.className = 'alert-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(alertContainer);
    }
    
    alertContainer.appendChild(alertEl);
    setTimeout(() => alertEl.remove(), 3000);
}

async function loadUserData(existingUserInfo = null) {
    try {
        // Obtener el estado del 2FA cuando cargamos los datos del usuario
        const [userInfo, gdprData, twoFactorStatus] = await Promise.all([
            AuthService.getUserProfile(),
            AuthService.getGDPRSettings(),
            Auth2FA.get2FAStatus()
        ]);

        // Esperar a que el DOM esté actualizado
        await new Promise(resolve => setTimeout(resolve, 0));

        const userInfoContainer = document.getElementById('userInfo');
        if (!userInfoContainer) {
            throw new Error('Container userInfo no encontrado');
        }

        // Eliminar spinner si existe
        const loadingSpinner = userInfoContainer.querySelector('#loadingSpinner');
        if (loadingSpinner) {
            loadingSpinner.remove();
        }

        // Crear y añadir la información del usuario
        const userInfoElement = createUserInfoElement(userInfo);
        userInfoContainer.appendChild(userInfoElement);

        // Actualizar el resto de elementos
        updateFormFields(userInfo);
        if (gdprData) {
            updateGDPRContent(gdprData);
        }

        // Actualizar el estado del botón 2FA
        const toggle2FABtn = document.getElementById('toggle2FABtn');
        const buttonText = document.getElementById('2faButtonText');
        if (toggle2FABtn && buttonText) {
            toggle2FABtn.dataset.enabled = twoFactorStatus.toString();
            buttonText.textContent = twoFactorStatus ? 'Desactivar 2FA' : 'Activar 2FA';
            toggle2FABtn.classList.remove('btn-outline-info', 'btn-outline-warning');
            toggle2FABtn.classList.add(twoFactorStatus ? 'btn-outline-warning' : 'btn-outline-info');
            
            // Guardar el estado en localStorage
            if (twoFactorStatus) {
                localStorage.setItem('two_factor_enabled', 'true');
            } else {
                localStorage.removeItem('two_factor_enabled');
            }
        }

    } catch (error) {
        console.error('Error cargando datos:', error);
        showAlert('Error cargando datos: ' + error.message, 'danger');
    }
}

// Nueva función auxiliar para actualizar campos del formulario
function updateFormFields(userInfo) {
    // Configurar campos
    const emailElement = document.getElementById('editEmail');
    const usernameElement = document.getElementById('editUsername');

    // Configurar username
    if (usernameElement) {
        usernameElement.value = userInfo.username;
        usernameElement.disabled = true;
        usernameElement.classList.add('form-control-disabled');
    }

    // Configurar email
    if (emailElement) {
        emailElement.value = userInfo.email;
        
        if (userInfo.is_fortytwo_user) {
            emailElement.disabled = true;
            emailElement.readOnly = true;
            emailElement.classList.add('form-control-disabled');
            
            // Mensaje informativo
            const helpText = emailElement.parentNode.querySelector('.form-text') || 
                           document.createElement('small');
            helpText.className = 'form-text text-muted mt-1';
            helpText.textContent = 'El email no se puede modificar para usuarios de 42';
            if (!emailElement.parentNode.querySelector('.form-text')) {
                emailElement.parentNode.appendChild(helpText);
            }

            // Ocultar sección de contraseña y botón guardar
            const securitySection = document.querySelector('.edit-section:has(.fa-shield-alt)');
            if (securitySection) securitySection.style.display = 'none';
            
            const saveButton = document.getElementById('saveProfileBtn');
            if (saveButton) saveButton.style.display = 'none';
        }
    }

    // Actualizar los colores de los labels
    document.querySelectorAll('.form-label').forEach(label => {
        label.classList.remove('text-muted');
    });
}

// Reemplazar la función updateGDPRContent actual con esta
function updateGDPRContent() {
    const gdprInfo = {
        'data-collection': [
            "Nombre de usuario y correo electrónico para identificación",
            "Datos de inicio de sesión y actividad de la cuenta",
            "Imagen de perfil (opcional)",
            "Información de autenticación de dos factores (si está activada)",
            "Datos de integración con 42 (si aplica)"
        ],
        'data-usage': [
            "Autenticación y gestión de tu cuenta",
            "Comunicaciones importantes sobre tu cuenta y seguridad",
            "Mejora de nuestros servicios y experiencia de usuario",
            "Cumplimiento de obligaciones legales y regulatorias"
        ],
        'user-rights': [
            "Derecho de acceso: Puedes descargar todos tus datos personales",
            "Derecho al olvido: Puedes solicitar la eliminación de tu cuenta",
            "Derecho de rectificación: Puedes modificar tus datos personales",
            "Derecho de portabilidad: Puedes exportar tus datos en formato JSON",
            "Derecho de oposición: Puedes desactivar funcionalidades opcionales"
        ],
        'security-measures': [
            "Encriptación de datos sensibles",
            "Autenticación de dos factores opcional",
            "Anonimización de datos en caso de eliminación de cuenta",
            "Auditoría de accesos y cambios en datos personales",
            "Almacenamiento seguro de contraseñas mediante hash"
        ],
        'data-retention': [
            "Tus datos se mantienen mientras tu cuenta esté activa",
            "Al eliminar tu cuenta, tus datos son anonimizados",
            "Mantenemos logs anonimizados por razones de seguridad",
            "Los backups se eliminan según política de retención"
        ]
    };

    Object.entries(gdprInfo).forEach(([id, items]) => {
        const element = document.getElementById(id);
        if (element) {
            element.innerHTML = items
                .map(item => `<div class="mb-2"><i class="fas fa-check text-success me-2"></i>${item}</div>`)
                .join('');
        }
    });
}

// Añadir las nuevas funciones para manejar las acciones de GDPR
async function handleDataDownload() {
	try {
		// Mostrar indicador de estado
		const downloadDataBtn = document.getElementById('downloadDataBtn');
		if (downloadDataBtn) {
			downloadDataBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Descargando...';
			downloadDataBtn.disabled = true;
		}

		// IMPORTANTE: Usar AuthGDPR directamente, no AuthService
		await AuthGDPR.downloadUserData();

		showAlert('Datos descargados correctamente', 'success');
	} catch (error) {
		console.error('Error al descargar datos:', error);
		showAlert('Error al descargar los datos: ' + error.message, 'danger');
	} finally {
		// Restaurar el botón
		const downloadDataBtn = document.getElementById('downloadDataBtn');
		if (downloadDataBtn) {
			downloadDataBtn.innerHTML = '<i class="fas fa-download me-2"></i>Descargar mis datos';
			downloadDataBtn.disabled = false;
		}
	}
}

async function handleDataDeletion() {
    if (confirm('¿Estás seguro de que quieres solicitar la eliminación de tus datos? Esta acción no se puede deshacer.')) {
        try {
            await AuthService.requestDataDeletion();
            showAlert('Solicitud de eliminación enviada correctamente', 'success');
        } catch (error) {
            showAlert('Error al solicitar la eliminación: ' + error.message, 'danger');
        }
    }
}

function createUserInfoElement(userInfo) {
    const template = document.getElementById('userInfoTemplate');
    if (!template) {
        throw new Error('Template no encontrado');
    }
    
    const element = template.content.cloneNode(true);
    const profileImage = element.querySelector('#profileImage');
    
    // Determinar la imagen correcta - profile_image tiene prioridad
    let imageUrl = userInfo.profile_image;
    if (!imageUrl) {
        imageUrl = userInfo.is_fortytwo_user ? 
            userInfo.fortytwo_image : 
            `https://api.dicebear.com/7.x/avataaars/svg?seed=${userInfo.username}`;
    }
    
    profileImage.src = imageUrl;
    
    const statusBadge = element.querySelector('#profileStatus .badge');
    statusBadge.className = `badge ${userInfo.is_active ? 'bg-success' : 'bg-warning'}`;
    statusBadge.textContent = userInfo.is_active ? 'Activo' : 'Pendiente';
    
    return element;
}
