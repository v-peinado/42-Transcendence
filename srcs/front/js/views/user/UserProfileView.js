import AuthService from '../../services/AuthService.js';
import { getNavbarHTML } from '../../components/Navbar.js';  // Añadir esta importación

export function UserProfileView() {
    const app = document.getElementById('app');
    
    app.innerHTML = `
        ${getNavbarHTML(true)}
        <!-- Input oculto para la imagen - IMPORTANTE: debe estar fuera del contenedor principal -->
        <input type="file" id="imageInput" accept="image/*" style="display: none">
        
        <div class="profile-section">
            <div class="container">
                <!-- Navegación por pestañas -->
                <ul class="nav nav-tabs profile-tabs mb-4" role="tablist">
                    <li class="nav-item" role="presentation">
                        <button class="nav-link active" data-bs-toggle="tab" data-bs-target="#profile">
                            <i class="fas fa-user me-2"></i>Perfil
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" data-bs-toggle="tab" data-bs-target="#stats">
                            <i class="fas fa-chart-line me-2"></i>Estadísticas
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" data-bs-toggle="tab" data-bs-target="#matches">
                            <i class="fas fa-trophy me-2"></i>Partidas
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" data-bs-toggle="tab" data-bs-target="#settings">
                            <i class="fas fa-cog me-2"></i>Ajustes
                        </button>
                    </li>
                </ul>

                <!-- Contenido de las pestañas -->
                <div class="tab-content">
                    <!-- Pestaña de Perfil -->
                    <div class="tab-pane fade show active" id="profile">
                        <div class="row justify-content-center">
                            <div class="col-md-6">
                                <div class="profile-card p-4" id="userInfo">
                                    <!-- Este div se llena dinámicamente con loadUserData -->
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Pestaña de Estadísticas -->
                    <div class="tab-pane fade" id="stats">
                        <div class="row g-4">
                            <div class="col-md-4">
                                <div class="stats-card">
                                    <h5>Ranking Global</h5>
                                    <div class="stat-value">#42</div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="stats-card">
                                    <h5>Victorias</h5>
                                    <div class="stat-value">75%</div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="stats-card">
                                    <h5>Puntuación</h5>
                                    <div class="stat-value">1842</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Pestaña de Partidas -->
                    <div class="tab-pane fade" id="matches">
                        <div class="matches-list">
                            <!-- Aquí irá el historial de partidas -->
                        </div>
                    </div>

                    <!-- Pestaña de Ajustes -->
                    <div class="tab-pane fade" id="settings">
                        <div class="row g-4">
                            <div class="col-md-6">
                                <div class="settings-card">
                                    <h5>Cuenta</h5>
                                    <div class="settings-actions">
                                        <button id="editProfileBtn" class="btn btn-outline-light d-flex align-items-center w-100 mb-3">
                                            <i class="fas fa-edit me-2"></i>
                                            <span>Editar Perfil</span>
                                            <i class="fas fa-chevron-right ms-auto"></i>
                                        </button>
                                        <button id="toggle2FABtn" class="btn btn-outline-info d-flex align-items-center w-100 mb-3">
                                            <i class="fas fa-shield-alt me-2"></i>
                                            <span id="2faButtonText">2FA</span>
                                            <i class="fas fa-chevron-right ms-auto"></i>
                                        </button>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="settings-card">
                                    <h5>Seguridad</h5>
                                    <div class="settings-actions">
                                        <button id="showQRBtn" class="btn btn-outline-primary d-flex align-items-center w-100 mb-3">
                                            <i class="fas fa-qrcode me-2"></i>
                                            <span>Código QR</span>
                                            <i class="fas fa-chevron-right ms-auto"></i>
                                        </button>
                                        <button id="gdprSettingsBtn" class="btn btn-outline-warning d-flex align-items-center w-100">
                                            <i class="fas fa-user-shield me-2"></i>
                                            <span>Privacidad</span>
                                            <i class="fas fa-chevron-right ms-auto"></i>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Añadir el modal al body
    const modalHTML = `
        <div class="modal fade" id="editProfileModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content bg-dark">
                    <div class="modal-header">
                        <h5 class="modal-title">Editar Perfil</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <!-- Añadir div para mensajes -->
                        <div id="modalMessage" class="alert d-none mb-3"></div>
                        <form id="editProfileForm">
                            <div class="mb-3">
                                <label class="form-label">Username</label>
                                <input type="text" class="form-control" id="editUsername" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Email</label>
                                <input type="email" class="form-control" id="editEmail" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Contraseña Actual</label>
                                <input type="password" class="form-control" id="currentPassword">
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Nueva Contraseña</label>
                                <input type="password" class="form-control" id="newPassword1">
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Confirmar Nueva Contraseña</label>
                                <input type="password" class="form-control" id="newPassword2">
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-outline-danger me-auto" id="deleteAccountBtn">
                            <i class="fas fa-trash-alt me-2"></i>Eliminar Cuenta
                        </button>
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                        <button type="button" class="btn btn-primary" id="saveProfileBtn">Guardar</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHTML);

    // Modificar el modal de eliminación de cuenta
    const deleteAccountModal = `
        <div class="modal fade" id="deleteAccountModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content bg-dark">
                    <div class="modal-header">
                        <h5 class="modal-title text-danger">Eliminar Cuenta</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="alert alert-warning">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            <strong>¡ATENCIÓN!</strong> Esta acción eliminará permanentemente:
                            <ul class="mt-2 mb-0">
                                <li>Tu cuenta y perfil</li>
                                <li>Todo tu historial de partidas</li>
                                <li>Tus estadísticas y logros</li>
                            </ul>
                        </div>
                        <form id="deleteAccountForm">
                            <div class="mb-3">
                                <label class="form-label">Confirma tu contraseña</label>
                                <input type="password" class="form-control" id="deleteAccountPassword" required>
                            </div>
                            <div class="form-check mb-3">
                                <input type="checkbox" class="form-check-input" id="confirmDelete" required>
                                <label class="form-check-label" for="confirmDelete">
                                    Entiendo que esta acción no se puede deshacer
                                </label>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                        <button type="button" class="btn btn-danger" id="confirmDeleteBtn" disabled>
                            <i class="fas fa-trash-alt me-2"></i>Eliminar Cuenta
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', deleteAccountModal);

    // Añadir el modal de QR después del contenido existente
    const qrModalHTML = `
        <div class="modal fade" id="qrModal" tabindex="-1">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content bg-dark">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-qrcode me-2"></i>Tu código QR
                        </h5>
                        <button type="button" class="btn btn-info btn-sm ms-2" id="qrHelpBtn">
                            <i class="fas fa-info-circle"></i>
                        </button>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body text-center">
                        <!-- Contenedor de información colapsable -->
                        <div class="collapse" id="qrInfoCollapse">
                            <div class="modal-info-box mb-4">
                                <div class="info-section">
                                    <i class="fas fa-info-circle text-info"></i>
                                    <div class="info-content">
                                        <h6>¿Para qué sirve este código QR?</h6>
                                        <p>Este código QR te permite iniciar sesión rápidamente desde otro dispositivo escaneándolo, sin necesidad de introducir tu usuario y contraseña.</p>
                                    </div>
                                </div>
                                <div class="security-section">
                                    <i class="fas fa-shield-alt text-warning"></i>
                                    <div class="info-content">
                                        <h6 class="text-warning">Recomendación de seguridad:</h6>
                                        <p>Para proteger mejor tu cuenta, activa la autenticación de dos factores (2FA) si usas el inicio de sesión con QR.</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div id="qrContainer" class="mb-3">
                            <div class="spinner-border text-primary"></div>
                        </div>
                        <p class="text-muted mb-3">
                            Usa este código QR para iniciar sesión rápidamente desde tu móvil
                        </p>
                        <button class="btn btn-primary" id="downloadQRBtn">
                            <i class="fas fa-download me-2"></i>Descargar QR
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', qrModalHTML);

    // Añadir verificación de URL para email
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('email_verified') === 'true') {
        setTimeout(() => {
            loadUserData();
            // Limpiar el parámetro de la URL
            window.history.replaceState({}, document.title, window.location.pathname);
        }, 1000); // Pequeño delay para asegurar que el backend está actualizado
    }

    loadUserData();
    setupProfileEvents();

    // Añadir event listener para el botón de logout del navbar
    document.getElementById('navLogoutBtn')?.addEventListener('click', async () => {
        try {
            await AuthService.logout();
            localStorage.removeItem('isAuthenticated');
            localStorage.removeItem('username');
            window.location.href = '/';
        } catch (error) {
            console.error('Error en logout:', error);
        }
    });
}

function setupProfileEvents() {
    // Event listener para el botón de editar
    document.getElementById('editProfileBtn')?.addEventListener('click', () => {
        const modalElement = document.getElementById('editProfileModal');
        const modal = new bootstrap.Modal(modalElement);
        
        // Cargar datos actuales en el formulario
        const username = document.getElementById('profileUsername').textContent;
        const email = document.getElementById('profileEmail').textContent;
        
        document.getElementById('editUsername').value = username;
        document.getElementById('editEmail').value = email;
        
        // Asegurarnos que el campo email es editable
        document.getElementById('editEmail').removeAttribute('disabled');
        
        modal.show();
    });

    // Event listener para guardar cambios
    document.getElementById('saveProfileBtn')?.addEventListener('click', async () => {
        try {
            const updates = {};
            const modalElement = document.getElementById('editProfileModal');
            const modal = bootstrap.Modal.getInstance(modalElement);
            const messageDiv = document.getElementById('modalMessage');
            
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
                modal.hide();
                alert(`Se ha enviado un email de verificación a ${newEmail}. 
                      Por favor, revisa tu bandeja de entrada.`);
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
                    modal.hide();
                }, 3000);
            }
        } catch (error) {
            // Mostrar errores en el modal
            const messageDiv = document.getElementById('modalMessage');
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

    // Event listener para el botón de GDPR
    document.getElementById('gdprSettingsBtn').addEventListener('click', () => {
        window.location.href = '/gdpr-settings';
    });
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
        const userInfo = await AuthService.getUserProfile();
        console.log('UserInfo recibido:', userInfo);
        
        const profileImage = userInfo.profile_image || userInfo.fortytwo_image || 
                           `https://api.dicebear.com/7.x/avataaars/svg?seed=${userInfo.username}`;
        
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

    } catch (error) {
        console.error('Error cargando datos:', error);
        // Si hay error, mostrar estado por defecto
        const toggle2FABtn = document.getElementById('toggle2FABtn');
        const buttonText = document.getElementById('2faButtonText');
        toggle2FABtn.dataset.enabled = 'false';
        buttonText.textContent = 'Activar 2FA';
        toggle2FABtn.classList.replace('btn-outline-warning', 'btn-outline-info');
        localStorage.removeItem('two_factor_enabled');
    }
}
