import AuthService from '../../services/AuthService.js';
import { Auth2FA } from '../../services/auth/Auth2FA.js';
import { AuthGDPR } from '../../services/auth/AuthGDPR.js';
import { getNavbarHTML } from '../../components/Navbar.js';

const VALID_VIEWS = [
    '/views/user/UserProfile.html',
];

export async function UserProfileView() {
    document.body.setAttribute('data-page', 'profile');
    const app = document.getElementById('app');
    
    try {
        // 1. Obtener datos necesarios
        const [userInfo, twoFactorStatus] = await Promise.all([
            AuthService.getUserProfile(),
            Auth2FA.get2FAStatus()
        ]);
        const viewHtml = await fetch('/views/user/UserProfile.html').then(r => r.text());
        const navbar = await getNavbarHTML(true, userInfo, true);

        // 2. Crear contenedor temporal para parsear el HTML de forma segura
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = navbar + viewHtml;
        
        // 3. Limpiar y actualizar el DOM de forma segura
        while (app.firstChild) app.removeChild(app.firstChild);
        while (tempDiv.firstChild) app.appendChild(tempDiv.firstChild);

        // 4. Actualizar el perfil usando createElement
        const userInfoContainer = document.getElementById('userInfo');
        if (userInfoContainer) {
            const spinner = userInfoContainer.querySelector('#loadingSpinner');
            if (spinner) spinner.remove();

            // Crear elementos de forma segura
            const container = document.createElement('div');
            container.className = 'text-center';

            // Avatar container
            const avatarContainer = document.createElement('div');
            avatarContainer.className = 'position-relative mb-4 avatar-container';

            const img = document.createElement('img');
            img.id = 'profileImage';
            img.className = 'profile-avatar rounded-circle';
            img.alt = 'Profile';
            img.src = userInfo.profile_image || userInfo.fortytwo_image || 
                     `https://api.dicebear.com/7.x/avataaars/svg?seed=${userInfo.username}`;

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

            userInfoContainer.appendChild(container);
        }

        // Actualizar estado del botón 2FA
        const toggle2FABtn = document.getElementById('toggle2FABtn');
        const buttonText = document.getElementById('2faButtonText');
        if (toggle2FABtn && buttonText) {
            toggle2FABtn.dataset.enabled = twoFactorStatus.toString();
            buttonText.textContent = twoFactorStatus ? 'Desactivar 2FA' : 'Activar 2FA';
            toggle2FABtn.classList.remove('btn-outline-info', 'btn-outline-warning');
            toggle2FABtn.classList.add(twoFactorStatus ? 'btn-outline-warning' : 'btn-outline-info');
        }

        // 5. Inicializar funcionalidad
        initializeTabs();
        setupProfileEvents();
        updateFormFields(userInfo);

    } catch (error) {
        console.error('Error loading profile view:', error);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger m-3';
        errorDiv.textContent = `Error cargando el perfil: ${error.message}`;
        app.appendChild(errorDiv);
    }

    console.log('Templates disponibles:', {
        userInfoTemplate: document.getElementById('userInfoTemplate'),
        profileModals: document.getElementById('profileModals'),
        alertTemplate: document.getElementById('alertTemplate')
    });
}

function cleanupTemplates() {
    const templates = document.querySelectorAll('template');
    templates.forEach(template => {
        if (template.id.startsWith('userInfo') || 
            template.id.startsWith('alert') || 
            template.id.startsWith('modal')) {
            template.remove();
        }
    });
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

            if (result.requiresVerification) {
                messageDiv.classList.remove('d-none', 'alert-danger');
                messageDiv.classList.add('alert-success');
                messageDiv.innerHTML = `
                    <i class="fas fa-info-circle me-2"></i>
                    Se ha enviado un email de verificación a ${updates.email}. 
                    Por favor, revisa tu bandeja de entrada.
                `;
            } else if (updates.current_password) {
                messageDiv.classList.remove('d-none', 'alert-danger');
                messageDiv.classList.add('alert-success');
                messageDiv.innerHTML = `
                    <i class="fas fa-check-circle me-2"></i>
                    ${result.message || 'Tu contraseña ha sido actualizada correctamente'}
                `;
                
                // Limpiar los campos de contraseña
                document.getElementById('currentPassword').value = '';
                document.getElementById('newPassword1').value = '';
                document.getElementById('newPassword2').value = '';
                
                // Ocultar el mensaje después de 3 segundos y cerrar el modal
                setTimeout(() => {
                    messageDiv.classList.add('d-none');
                }, 3000);
            }
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

                if (!file.type.startsWith('image/')) {
                    alertEl.className = 'alert alert-danger';
                    alertEl.textContent = 'Por favor, selecciona una imagen válida';
                    alertEl.style.display = 'block';
                    return;
                }

                const userInfo = await AuthService.updateProfileImage(file);
                
                if (userInfo && userInfo.profile_image) {
                    // Actualizar todas las instancias de la imagen inmediatamente
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
                alertEl.textContent = error.message;
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
            const userInfo = await AuthService.updateProfile({ restore_image: true });
            
            // Actualizar todas las instancias de la imagen inmediatamente
            const imageUrl = userInfo.profile_image || 
                           userInfo.fortytwo_image || 
                           `https://api.dicebear.com/7.x/avataaars/svg?seed=${userInfo.username}`;
            
            const imageElements = document.querySelectorAll('#profileImage, #navbarUserAvatar, #dropdownUserAvatar');
            imageElements.forEach(el => {
                if (el) el.src = imageUrl;
            });

            alertEl.className = 'alert alert-success';
            alertEl.textContent = 'Imagen restaurada correctamente';
            
            // Resetear el input
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
            console.log('Iniciando generación de QR...');
            const template = document.getElementById('qrModalTemplate');
            if (!template) throw new Error('Template QR no encontrado');
            
            // Clonar y añadir el modal al DOM
            const modalElement = template.content.cloneNode(true);
            document.body.appendChild(modalElement);
            
            // Inicializar y mostrar el modal
            const modal = new bootstrap.Modal(document.getElementById('qrModal'));
            modal.show();
            
            const username = localStorage.getItem('username');
            console.log('Generando QR para usuario:', username);
            // Cambiar AuthService por Auth2FA
            const qrUrl = await Auth2FA.generateQR(username);
            console.log('QR URL generada:', qrUrl);
            
            const qrContainer = document.getElementById('qrContainer');
            const qrImage = new Image();
            qrImage.src = qrUrl;
            qrImage.alt = 'QR Code';
            qrImage.className = 'img-fluid';
            qrImage.style.maxWidth = '256px';
            
            qrImage.onload = () => {
                console.log('QR imagen cargada, dimensiones:', qrImage.naturalWidth, 'x', qrImage.naturalHeight);
                qrContainer.innerHTML = '';
                qrContainer.appendChild(qrImage);
                
                const downloadBtn = document.getElementById('downloadQRBtn');
                console.log('Botón de descarga encontrado:', !!downloadBtn);
                if (downloadBtn) {
                    downloadBtn.addEventListener('click', () => {
                        console.log('Click en botón de descarga');
                        const canvas = document.createElement('canvas');
                        canvas.width = qrImage.naturalWidth;
                        canvas.height = qrImage.naturalHeight;
                        const ctx = canvas.getContext('2d');
                        ctx.drawImage(qrImage, 0, 0);
                        
                        const link = document.createElement('a');
                        link.download = `qr-login-${username}.png`;
                        link.href = canvas.toDataURL('image/png');
                        console.log('Iniciando descarga del QR');
                        link.click();
                    });
                }
            };

            qrImage.onerror = (error) => {
                console.error('Error al cargar la imagen QR:', error);
            };

        } catch (error) {
            console.error('Error al generar el código QR:', error);
            showAlert('Error al generar el código QR: ' + error.message, 'danger');
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

	// Añadir manejador para el botón de descarga GDPR
	const setupGDPRTab = () => {
		const downloadDataBtn = document.getElementById('downloadDataBtn');
		if (downloadDataBtn) {
			downloadDataBtn.addEventListener('click', async () => {
				try {
					// Mostrar indicador de carga
					downloadDataBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Descargando...';
					downloadDataBtn.disabled = true;

					// Importante: Usar directamente AuthGDPR en lugar de AuthService
					const result = await AuthGDPR.downloadUserData();

					if (result.status === 'error') {
						showAlert('danger', 'Error al descargar datos', result.message);
					} else {
						showAlert('success', 'Datos descargados', 'Tus datos personales han sido descargados');
					}
				} catch (error) {
					console.error('Error downloading data:', error);
					showAlert('danger', 'Error', 'Ha ocurrido un error al descargar tus datos');
				} finally {
					// Restaurar el botón
					downloadDataBtn.innerHTML = '<i class="fas fa-download me-2"></i>Descargar mis datos';
					downloadDataBtn.disabled = false;
				}
			});
		}
	};
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

// Añadir la función updateGDPRContent
function updateGDPRContent(data) {
    const sections = {
        'data-collection': data.gdpr_policy?.data_collection || [],
        'data-usage': data.gdpr_policy?.data_usage || [],
        'user-rights': data.gdpr_policy?.user_rights || [],
        'security-measures': data.gdpr_policy?.security_measures || []
    };

    Object.entries(sections).forEach(([id, items]) => {
        const element = document.getElementById(id);
        if (element && Array.isArray(items)) {
            element.textContent = ''; // Limpiar contenido existente
            items.forEach(item => {
                const div = document.createElement('div');
                div.className = 'mb-2';
                div.textContent = item;
                element.appendChild(div);
            });
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
    // Obtener el template
    const template = document.getElementById('userInfoTemplate');
    if (!template) {
        throw new Error('Template no encontrado');
    }
    
    // Clonar el template
    const element = template.content.cloneNode(true);
    
    // Actualizar los elementos
    const profileImage = element.querySelector('#profileImage');
    profileImage.src = userInfo.profile_image || 
                      userInfo.fortytwo_image || 
                      `https://api.dicebear.com/7.x/avataaars/svg?seed=${userInfo.username}`;
    const statusBadge = element.querySelector('#profileStatus .badge');
    statusBadge.className = `badge ${userInfo.is_active ? 'bg-success' : 'bg-warning'}`;
    statusBadge.textContent = userInfo.is_active ? 'Activo' : 'Pendiente';
    
    return element;
}

async function handleEmailChange(e) {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const alertContainer = document.getElementById('profileAlert');
    const submitButton = e.target.querySelector('button[type="submit"]');
    
    try {
        submitButton.disabled = true;
        const result = await AuthService.updateProfile({ email });
        
        if (result.status === 'rate_limit') {
            alertContainer.innerHTML = `
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
                alertContainer.innerHTML = '';
            }, result.remaining_time * 1000);
            return;
        }

        if (result.success || result.requiresVerification) {
            alertContainer.innerHTML = `
                <div class="alert alert-success fade show">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-check-circle fa-2x me-3"></i>
                        <div>
                            <h6 class="alert-heading mb-1">¡Email actualizado!</h6>
                            <span>Se ha enviado un email de verificación a ${email}</span>
                        </div>
                    </div>
                </div>`;
            
            setTimeout(() => {
                alertContainer.innerHTML = '';
            }, 5000);
        }
    } catch (error) {
        submitButton.disabled = false;
        alertContainer.innerHTML = `
            <div class="alert alert-danger fade show">
                <div class="d-flex align-items-center">
                    <i class="fas fa-exclamation-circle fa-2x me-3"></i>
                    <div>
                        <h6 class="alert-heading mb-1">Error</h6>
                        <span>${error.message || 'Error al actualizar el email'}</span>
                    </div>
                </div>
            </div>`;
        
        setTimeout(() => {
            alertContainer.innerHTML = '';
        }, 5000);
    } finally {
        submitButton.disabled = false;
    }
}
