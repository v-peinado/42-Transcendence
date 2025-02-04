import AuthService from '../../services/AuthService.js';
import { Auth2FA } from '../../services/auth/Auth2FA.js';
import { getNavbarHTML } from '../../components/Navbar.js';

const VALID_VIEWS = [
    '/views/user/UserProfile.html',
    // ...other valid views
];

export async function UserProfileView() {
    document.body.setAttribute('data-page', 'profile');
    
    const app = document.getElementById('app');
    
    try {
        // Obtener la información del usuario antes de cargar el navbar
        const userInfo = await AuthService.getUserProfile();
        
        const viewPath = '/views/user/UserProfile.html';
        if (!VALID_VIEWS.includes(viewPath)) {
            throw new Error('Invalid view path');
        }
        
        // Cargar el contenido HTML desde el archivo
        const response = await fetch(viewPath);
        const html = await response.text();
        
        // Insertar el HTML y el navbar con los parámetros correctos
        app.innerHTML = `
            ${await getNavbarHTML(true, userInfo, true)}
            ${html}
        `;

        // Inicializar las pestañas de Bootstrap después de cargar el contenido
        const tabElements = document.querySelectorAll('[data-bs-toggle="tab"]');
        tabElements.forEach(tab => {
            const tabTrigger = new bootstrap.Tab(tab);
            
            // Eliminar las transiciones por defecto de Bootstrap
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = tab.dataset.bsTarget;
                document.querySelectorAll('.tab-pane').forEach(pane => {
                    pane.classList.remove('active', 'show');
                });
                document.querySelector(targetId).classList.add('active', 'show');
                
                // Actualizar estado activo de las pestañas
                document.querySelectorAll('.nav-link').forEach(link => {
                    link.classList.remove('active');
                });
                tab.classList.add('active');
            });
        });

        // Cargar los modales desde el template
        const modalsTemplate = document.getElementById('profileModals');
        if (modalsTemplate) {
            document.body.appendChild(modalsTemplate.content.cloneNode(true));
        }

        loadUserData();
        setupProfileEvents();
    } catch (error) {
        console.error('Error loading profile view:', error);
        app.innerHTML = '<div class="alert alert-danger">Error loading profile</div>';
    }

    return () => {
        document.body.removeAttribute('data-page');
    };
}

function setupProfileEvents() {
    // Eliminar el event listener del botón de editar ya que ahora usamos pestañas
    // Actualizar el event listener para guardar cambios
    document.getElementById('saveProfileBtn')?.addEventListener('click', async () => {
        try {
            const updates = {};
            const messageDiv = document.getElementById('editProfileMessage');
            
            // Verificar cambios de email
            const newEmail = document.getElementById('editEmail').value;
            const currentEmail = document.getElementById('profileEmail').textContent;
            if (newEmail !== currentEmail) {
                updates.email = newEmail;
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
            
            if (result.requiresVerification) {
                messageDiv.classList.remove('d-none', 'alert-danger');
                messageDiv.classList.add('alert-success');
                messageDiv.innerHTML = `
                    <i class="fas fa-info-circle me-2"></i>
                    Se ha enviado un email de verificación a ${newEmail}. 
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

    // Event listener para mostrar modal de eliminar cuenta
    document.getElementById('deleteAccountBtn')?.addEventListener('click', () => {
        const editModal = bootstrap.Modal.getInstance(document.getElementById('editProfileModal'));
        editModal.hide();
        const deleteModal = new bootstrap.Modal(document.getElementById('deleteAccountModal'));
        deleteModal.show();
    });

    // Event listener para confirmar eliminación
    document.getElementById('confirmDeleteBtn')?.addEventListener('click', async () => {
        try {
            const password = document.getElementById('deleteAccountPassword').value;
            if (!password) {
                throw new Error('Debes introducir tu contraseña');
            }

            const result = await AuthService.deleteAccount(password);
            if (result.success) {
                window.location.href = '/';
            }
        } catch (error) {
            const messageDiv = document.getElementById('modalMessage');
            messageDiv.classList.remove('d-none', 'alert-success');
            messageDiv.classList.add('alert-danger');
            messageDiv.innerHTML = `
                <i class="fas fa-exclamation-circle me-2"></i>
                ${error.message || 'Error al eliminar la cuenta'}
            `;
        }
    });

    // Event listener para el checkbox de confirmación
    document.getElementById('confirmDelete')?.addEventListener('change', (e) => {
        document.getElementById('confirmDeleteBtn').disabled = !e.target.checked;
    });

    // Añade estos event listeners después de renderizar el template
    document.getElementById('changeImageBtn')?.addEventListener('click', () => {
        document.getElementById('imageInput').click();
    });

    document.getElementById('imageInput')?.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        const alertEl = document.getElementById('imageAlert');
        
        if (file) {
            // Validar tamaño y tipo
            if (file.size > 5 * 1024 * 1024) {
                alertEl.className = 'alert alert-danger';
                alertEl.textContent = 'La imagen no debe superar 5MB';
                alertEl.style.display = 'block';
                return;
            }

            if (!file.type.startsWith('image/')) {
                alertEl.className = 'alert alert-danger';
                alertEl.textContent = 'Por favor, selecciona una imagen válida';
                alertEl.style.display = 'block';
                return;
            }

            try {
                const userInfo = await AuthService.updateProfileImage(file);
                
                if (userInfo && userInfo.profile_image) {
                    // Actualizar todas las instancias de la imagen con la URL del backend
                    const imageUrl = userInfo.profile_image;
                    
                    const imageElements = [
                        document.getElementById('profileImage'),
                        document.getElementById('navbarUserAvatar'),
                        document.getElementById('dropdownUserAvatar')
                    ];

                    imageElements.forEach(el => {
                        if (el) {
                            el.src = imageUrl;
                        }
                    });

                    alertEl.className = 'alert alert-success';
                    alertEl.textContent = 'Imagen actualizada correctamente';
                } else {
                    throw new Error('Error al actualizar la imagen');
                }
                
                alertEl.style.display = 'block';
            } catch (error) {
                alertEl.className = 'alert alert-danger';
                alertEl.textContent = error.message;
                alertEl.style.display = 'block';
            }
        }
    });

    document.getElementById('restoreImageBtn')?.addEventListener('click', async () => {
        const alertEl = document.getElementById('imageAlert');
        
        try {
            const userInfo = await AuthService.updateProfile({ restore_image: true });
            
            // Actualizar la imagen mostrada inmediatamente con la respuesta del backend
            const profileImage = document.getElementById('profileImage');
            const navbarAvatar = document.getElementById('navbarUserAvatar');
            const dropdownAvatar = document.getElementById('dropdownUserAvatar');
            
            const imageUrl = userInfo.profile_image || // usar la imagen del perfil si existe
                            userInfo.fortytwo_image || // o la imagen de 42 si es usuario de 42
                            `https://api.dicebear.com/7.x/avataaars/svg?seed=${userInfo.username}`; // o dicebear como último recurso
            
            const imageElements = [profileImage, navbarAvatar, dropdownAvatar];
            imageElements.forEach(el => {
                if (el) {
                    el.src = imageUrl;
                    // Solo usar dicebear como fallback si la imagen principal falla
                    el.onerror = function() {
                        const username = localStorage.getItem('username');
                        this.src = `https://api.dicebear.com/7.x/avataaars/svg?seed=${username}`;
                    };
                }
            });

            alertEl.className = 'alert alert-success';
            alertEl.textContent = 'Imagen restaurada correctamente';
            alertEl.style.display = 'block';
        } catch (error) {
            alertEl.className = 'alert alert-danger';
            alertEl.textContent = error.message;
            alertEl.style.display = 'block';
        }
    });

    // Event listener para el botón de 2FA
    document.getElementById('toggle2FABtn')?.addEventListener('click', async () => {
        try {
            const button = document.getElementById('toggle2FABtn');
            const buttonText = document.getElementById('2faButtonText');
            const is2FAEnabled = button.dataset.enabled === 'true';

            if (!is2FAEnabled) {
                // Crear el modal de confirmación
                const modalHTML = `
                    <div class="modal fade" id="confirm2FAModal" tabindex="-1">
                        <div class="modal-dialog modal-dialog-centered">
                            <div class="modal-content bg-dark">
                                <div class="modal-header">
                                    <h5 class="modal-title">
                                        <i class="fas fa-shield-alt me-2"></i>Activar 2FA
                                    </h5>
                                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                                </div>
                                <div class="modal-body">
                                    <div class="modal-info-box">
                                        <div class="info-section">
                                            <i class="fas fa-info-circle text-info"></i>
                                            <div class="info-content">
                                                <h6>Autenticación en dos pasos</h6>
                                                <p>La autenticación en dos pasos añade una capa extra de seguridad a tu cuenta. 
                                                Cada vez que inicies sesión, necesitarás introducir un código que te enviaremos por email.</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                                    <button type="button" class="btn btn-primary" id="confirm2FABtn">
                                        <i class="fas fa-check me-2"></i>Activar
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;

                // Añadir el modal al DOM
                document.body.insertAdjacentHTML('beforeend', modalHTML);

                // Inicializar y mostrar el modal
                const modalElement = document.getElementById('confirm2FAModal');
                const modal = new bootstrap.Modal(modalElement);
                modal.show();

                // Event listener para el botón de confirmar
                document.getElementById('confirm2FABtn').addEventListener('click', async () => {
                    const result = await AuthService.enable2FA();
                    if (result.success) {
                        button.dataset.enabled = 'true';
                        buttonText.textContent = 'Desactivar 2FA';
                        button.classList.replace('btn-outline-info', 'btn-outline-warning');
                        localStorage.setItem('two_factor_enabled', 'true');
                        modal.hide();
                        
                        // Eliminar el modal del DOM después de ocultarlo
                        modalElement.addEventListener('hidden.bs.modal', () => {
                            modalElement.remove();
                        });
                    }
                });

                // Limpiar el modal cuando se cierre
                modalElement.addEventListener('hidden.bs.modal', () => {
                    modalElement.remove();
                });
            } else {
                // Crear el modal de desactivación
                const modalHTML = `
                    <div class="modal fade" id="disable2FAModal" tabindex="-1">
                        <div class="modal-dialog modal-dialog-centered">
                            <div class="modal-content bg-dark">
                                <div class="modal-header">
                                    <h5 class="modal-title">
                                        <i class="fas fa-shield-alt me-2"></i>Desactivar 2FA
                                    </h5>
                                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                                </div>
                                <div class="modal-body">
                                    <div class="modal-info-box">
                                        <div class="info-section">
                                            <i class="fas fa-exclamation-triangle text-warning"></i>
                                            <div class="info-content">
                                                <h6 class="text-warning">¿Estás seguro?</h6>
                                                <p>Al desactivar la autenticación en dos pasos, tu cuenta será menos segura.</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                                    <button type="button" class="btn btn-warning" id="confirm2FADisableBtn">
                                        <i class="fas fa-shield-alt me-2"></i>Desactivar
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;

                // Añadir el modal al DOM
                document.body.insertAdjacentHTML('beforeend', modalHTML);

                // Inicializar y mostrar el modal
                const modalElement = document.getElementById('disable2FAModal');
                const modal = new bootstrap.Modal(modalElement);
                modal.show();

                // Event listener para el botón de confirmar desactivación
                document.getElementById('confirm2FADisableBtn').addEventListener('click', async () => {
                    const result = await AuthService.disable2FA();
                    if (result.success) {
                        button.dataset.enabled = 'false';
                        buttonText.textContent = 'Activar 2FA';
                        button.classList.replace('btn-outline-warning', 'btn-outline-info');
                        localStorage.removeItem('two_factor_enabled');
                        modal.hide();
                        
                        // Eliminar el modal del DOM después de ocultarlo
                        modalElement.addEventListener('hidden.bs.modal', () => {
                            modalElement.remove();
                        });
                    }
                });

                // Limpiar el modal cuando se cierre
                modalElement.addEventListener('hidden.bs.modal', () => {
                    modalElement.remove();
                });
            }
        } catch (error) {
            showAlert(error.message, 'danger');
        }
    });

    // Añadir el event listener para el botón QR
    document.getElementById('showQRBtn')?.addEventListener('click', async () => {
        const modal = new bootstrap.Modal(document.getElementById('qrModal'));
        modal.show();
        
        try {
            const username = localStorage.getItem('username');
            const qrUrl = await AuthService.generateQR(username);
            
            document.getElementById('qrContainer').innerHTML = `
                <img src="${qrUrl}" alt="QR Code" class="img-fluid" style="max-width: 256px;">
            `;
        } catch (error) {
            document.getElementById('qrContainer').innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    Error generando el código QR
                </div>
            `;
        }
    });

    document.getElementById('downloadQRBtn')?.addEventListener('click', () => {
        const qrImage = document.querySelector('#qrContainer img');
        if (qrImage) {
            // Crear un canvas temporal
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            // Configurar el tamaño del canvas al tamaño de la imagen
            canvas.width = qrImage.naturalWidth;
            canvas.height = qrImage.naturalHeight;
            
            // Dibujar la imagen en el canvas
            ctx.drawImage(qrImage, 0, 0);
            
            // Crear un link temporal y descargar
            const link = document.createElement('a');
            const username = localStorage.getItem('username');
            link.download = `qr-login-${username}.png`;
            link.href = canvas.toDataURL('image/png');
            link.click();
        }
    });

    // Añadir el event listener para el botón de ayuda
    document.getElementById('qrHelpBtn')?.addEventListener('click', () => {
        const collapseElement = document.getElementById('qrInfoCollapse');
        const collapse = new bootstrap.Collapse(collapseElement, {
            toggle: true
        });
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
}

// Función auxiliar para mostrar alertas
function showAlert(message, type) {
    const alertEl = document.createElement('div');
    alertEl.className = `alert alert-${type} fade show`;
    alertEl.role = 'alert';
    alertEl.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
        <div class="alert-content">
            <p>${message}</p>
        </div>
    `;
    
    // Insertar alerta después del botón 2FA
    const button2FA = document.getElementById('toggle2FABtn');
    button2FA.parentNode.insertBefore(alertEl, button2FA.nextSibling);
    
    // Remover después de 3 segundos
    setTimeout(() => alertEl.remove(), 3000);
}

async function loadUserData() {
    try {
        const [userInfo, gdprData] = await Promise.all([
            AuthService.getUserProfile(),
            AuthService.getGDPRSettings()
        ]);
        
        const profileImage = userInfo.profile_image || userInfo.fortytwo_image || 
                           `https://api.dicebear.com/7.x/avataaars/svg?seed=${userInfo.username}`;
        
        // Actualizar el estado del botón 2FA
        const toggle2FABtn = document.getElementById('toggle2FABtn');
        const buttonText = document.getElementById('2faButtonText');
        
        if (toggle2FABtn && buttonText) {
            const is2FAEnabled = Auth2FA.isEnabled;
            toggle2FABtn.dataset.enabled = is2FAEnabled.toString();
            buttonText.textContent = is2FAEnabled ? 'Desactivar 2FA' : 'Activar 2FA';
            toggle2FABtn.classList.remove('btn-outline-info', 'btn-outline-warning');
            toggle2FABtn.classList.add(is2FAEnabled ? 'btn-outline-warning' : 'btn-outline-info');
        }

        document.getElementById('userInfo').innerHTML = `
            <div class="text-center">
                <div class="position-relative mb-4 avatar-container">
                    <img src="${profileImage}" 
                         alt="Profile" 
                         class="profile-avatar rounded-circle"
                         id="profileImage"
                         onerror="this.src='https://api.dicebear.com/7.x/avataaars/svg?seed=${userInfo.username}'">
                    <div class="avatar-buttons">
                        <button class="btn btn-sm btn-primary rounded-circle" 
                                id="changeImageBtn">
                            <i class="fas fa-camera"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-light rounded-circle" 
                                id="restoreImageBtn">
                            <i class="fas fa-undo"></i>
                        </button>
                    </div>
                </div>
                <h3 class="mb-2" id="profileUsername">${userInfo.username}</h3>
                <p class="text-muted mb-3" id="profileEmail">${userInfo.email}</p>
                <div class="status-badge mb-4" id="profileStatus">
                    <span class="badge ${userInfo.is_active ? 'bg-success' : 'bg-warning'}">
                        ${userInfo.is_active ? 'Activo' : 'Pendiente'}
                    </span>
                </div>
            </div>
        `;

        // Volver a añadir los event listeners después de cargar el contenido
        document.getElementById('changeImageBtn')?.addEventListener('click', () => {
            document.getElementById('imageInput').click();
        });

        document.getElementById('restoreImageBtn')?.addEventListener('click', async () => {
            const alertEl = document.getElementById('imageAlert');
        
            try {
                const userInfo = await AuthService.updateProfile({ restore_image: true });
                
                // Actualizar la imagen mostrada inmediatamente con la respuesta del backend
                const profileImage = document.getElementById('profileImage');
                const navbarAvatar = document.getElementById('navbarUserAvatar');
                const dropdownAvatar = document.getElementById('dropdownUserAvatar');
                
                const imageUrl = userInfo.profile_image || // usar la imagen del perfil si existe
                                userInfo.fortytwo_image || // o la imagen de 42 si es usuario de 42
                                `https://api.dicebear.com/7.x/avataaars/svg?seed=${userInfo.username}`; // o dicebear como último recurso
                
                const imageElements = [profileImage, navbarAvatar, dropdownAvatar];
                imageElements.forEach(el => {
                    if (el) {
                        el.src = imageUrl;
                        // Solo usar dicebear como fallback si la imagen principal falla
                        el.onerror = function() {
                            const username = localStorage.getItem('username');
                            this.src = `https://api.dicebear.com/7.x/avataaars/svg?seed=${username}`;
                        };
                    }
                });

                alertEl.className = 'alert alert-success';
                alertEl.textContent = 'Imagen restaurada correctamente';
                alertEl.style.display = 'block';
            } catch (error) {
                alertEl.className = 'alert alert-danger';
                alertEl.textContent = error.message;
                alertEl.style.display = 'block';
            }
        });

        // Cargar datos en el formulario de edición
        document.getElementById('editUsername').value = userInfo.username;
        document.getElementById('editEmail').value = userInfo.email;

        // Actualizar secciones GDPR
        if (gdprData) {
            updateGDPRContent(gdprData);
        }

    } catch (error) {
        console.error('Error cargando datos:', error);
        const toggle2FABtn = document.getElementById('toggle2FABtn');
        const buttonText = document.getElementById('2faButtonText');
        const is2FAEnabled = Auth2FA.isEnabled;
        
        if (toggle2FABtn && buttonText) {
            toggle2FABtn.dataset.enabled = is2FAEnabled.toString();
            buttonText.textContent = is2FAEnabled ? 'Desactivar 2FA' : 'Activar 2FA';
            toggle2FABtn.classList.remove('btn-outline-info', 'btn-outline-warning');
            toggle2FABtn.classList.add(is2FAEnabled ? 'btn-outline-warning' : 'btn-outline-info');
        }
    }
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
            element.innerHTML = items
                .map(item => `<div class="mb-2">${item}</div>`)
                .join('');
        }
    });
}

// Añadir las nuevas funciones para manejar las acciones de GDPR
async function handleDataDownload() {
    try {
        const response = await AuthService.downloadUserData();
        // Crear un blob y descargarlo
        const blob = new Blob([JSON.stringify(response, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'mis-datos.json';
        a.click();
        window.URL.revokeObjectURL(url);
    } catch (error) {
        showAlert('Error al descargar los datos: ' + error.message, 'danger');
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
