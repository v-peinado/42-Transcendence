import AuthService from '../../services/AuthService.js';

export function UserProfileView() {
    const app = document.getElementById('app');
    const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
    const username = localStorage.getItem('username');
    
    app.innerHTML = `
        <!-- Navbar simplificado para perfil -->
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark fixed-top">
            <div class="container">
                <a class="navbar-brand d-flex align-items-center" href="/" data-link>
                    <svg class="logo me-2" width="32" height="32" viewBox="0 0 100 100">
                        <rect x="10" y="40" width="10" height="20" fill="#fff">
                            <animate attributeName="height" values="20;40;20" dur="1s" repeatCount="indefinite"/>
                        </rect>
                        <circle cx="50" cy="50" r="5" fill="#fff">
                            <animate attributeName="cx" values="50;52;50" dur="0.5s" repeatCount="indefinite"/>
                            <animate attributeName="cy" values="50;48;50" dur="0.5s" repeatCount="indefinite"/>
                        </circle>
                        <rect x="80" y="40" width="10" height="20" fill="#fff">
                            <animate attributeName="height" values="40;20;40" dur="1s" repeatCount="indefinite"/>
                        </rect>
                    </svg>
                    <span class="brand-text">Transcendence</span>
                </a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav me-auto">
                        <li class="nav-item">
                            <a class="nav-link" href="/game" data-link>
                                <i class="fas fa-play me-1"></i>Jugar
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/leaderboard" data-link>
                                <i class="fas fa-trophy me-1"></i>Clasificación
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/chat" data-link>
                                <i class="fas fa-comments me-1"></i>Chat
                            </a>
                        </li>
                    </ul>
                    <ul class="navbar-nav">
                        <li class="nav-item">
                            <a class="nav-link text-danger-hover" id="navLogoutBtn" href="#" style="cursor: pointer;">
                                <i class="fas fa-sign-out-alt me-2"></i>Salir
                            </a>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>

        <!-- Contenedor principal con padding ajustado -->
        <main class="profile-section">
            <div class="container py-4">
                <div class="row g-3">
                    <!-- Perfil Card Principal -->
                    <div class="col-lg-4">
                        <div class="card profile-card bg-dark text-light border-0 shadow h-100">
                            <div class="card-body p-4">
                                <div id="userInfo" class="text-center">
                                    <div class="placeholder-glow">
                                        <span class="placeholder col-6"></span>
                                    </div>
                                </div>
                                
                                <!-- Sección de imagen de perfil con nuevo estilo -->
                                <div class="text-center mt-4">
                                    <input type="file" 
                                           class="form-control bg-dark text-light" 
                                           id="imageInput" 
                                           accept="image/*" 
                                           style="display: none;">
                                    <div class="btn-group w-100">
                                        <button class="btn btn-primary" id="changeImageBtn">
                                            <i class="fas fa-camera me-2"></i>Cambiar Imagen
                                        </button>
                                        <button class="btn btn-outline-light" id="restoreImageBtn">
                                            <i class="fas fa-undo me-2"></i>Restaurar
                                        </button>
                                    </div>
                                    <div class="alert mt-3" id="imageAlert" style="display: none;"></div>
                                </div>
                                
                                <!-- Stats con nuevo diseño -->
                                <div class="row g-3 mt-4">
                                    <div class="col-4">
                                        <div class="bg-dark-subtle rounded p-3 text-center h-100">
                                            <i class="fas fa-trophy text-warning fs-4 mb-2"></i>
                                            <h3 class="fs-4 mb-0">25</h3>
                                            <small class="text-muted">Victorias</small>
                                        </div>
                                    </div>
                                    <div class="col-4">
                                        <div class="bg-dark-subtle rounded p-3 text-center h-100">
                                            <i class="fas fa-gamepad text-primary fs-4 mb-2"></i>
                                            <h3 class="fs-4 mb-0">42</h3>
                                            <small class="text-muted">Partidas</small>
                                        </div>
                                    </div>
                                    <div class="col-4">
                                        <div class="bg-dark-subtle rounded p-3 text-center h-100">
                                            <i class="fas fa-star text-info fs-4 mb-2"></i>
                                            <h3 class="fs-4 mb-0">8</h3>
                                            <small class="text-muted">Nivel</small>
                                        </div>
                                    </div>
                                </div>

                                <!-- Botones de acción con nuevo estilo -->
                                <div class="d-grid gap-2 mt-4">
                                    <a href="/game" class="btn btn-lg btn-primary">
                                        <i class="fas fa-gamepad me-2"></i>Jugar
                                    </a>
                                    <button id="editProfileBtn" class="btn btn-outline-light w-100">
                                        <i class="fas fa-cog me-2"></i>Configuración
                                    </button>
                                    <button id="toggle2FABtn" class="btn btn-outline-info">
                                        <i class="fas fa-shield-alt me-2"></i>
                                        <span id="2faButtonText">Activar 2FA</span>
                                    </button>
                                    <button id="showQRBtn" class="btn btn-outline-light w-100 mb-2">
                                        <i class="fas fa-qrcode me-2"></i>Ver código QR
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Panel derecho con información y estadísticas -->
                    <div class="col-lg-8">
                        <div class="row g-3">
                            <!-- Info Card con nuevo estilo -->
                            <div class="col-12">
                                <div class="card bg-dark text-light border-0 shadow">
                                    <div class="card-body p-4">
                                        <h5 class="card-title mb-4">
                                            <i class="fas fa-user me-2"></i>Información del Perfil
                                        </h5>
                                        <div class="row g-3">
                                            <div class="col-md-4">
                                                <small class="text-muted d-block">Username</small>
                                                <div id="profileUsername" class="fs-5">Cargando...</div>
                                            </div>
                                            <div class="col-md-4">
                                                <small class="text-muted d-block">Email</small>
                                                <div id="profileEmail" class="fs-5">Cargando...</div>
                                            </div>
                                            <div class="col-md-4">
                                                <small class="text-muted d-block">Estado</small>
                                                <div id="profileStatus">
                                                    <span class="badge bg-secondary">Cargando...</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Historial de Partidas con nuevo estilo -->
                            <div class="col-12">
                                <div class="card bg-dark text-light border-0 shadow">
                                    <div class="card-body p-4">
                                        <h5 class="card-title mb-4">
                                            <i class="fas fa-history me-2"></i>Historial de Partidas
                                        </h5>
                                        <div class="table-responsive">
                                            <table class="table table-dark table-hover">
                                                <thead>
                                                    <tr>
                                                        <th>Fecha</th>
                                                        <th>Oponente</th>
                                                        <th>Resultado</th>
                                                        <th>Puntos</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    <tr>
                                                        <td>2024-01-20</td>
                                                        <td>
                                                            <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Player123" 
                                                                 alt="Avatar" class="rounded-circle me-2" width="24" height="24">
                                                            Player123
                                                        </td>
                                                        <td><span class="badge bg-success">Victoria</span></td>
                                                        <td>10-8</td>
                                                    </tr>
                                                    <tr>
                                                        <td>2024-01-19</td>
                                                        <td>
                                                            <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=GameMaster" 
                                                                 alt="Avatar" class="rounded-circle me-2" width="24" height="24">
                                                            GameMaster
                                                        </td>
                                                        <td><span class="badge bg-danger">Derrota</span></td>
                                                        <td>5-10</td>
                                                    </tr>
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </main>
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
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body text-center">
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
                const confirmed = confirm(
                    'La autenticación en dos pasos añade una capa extra de seguridad a tu cuenta. ' +
                    'Cada vez que inicies sesión, necesitarás introducir un código que te enviaremos por email. ' +
                    '¿Deseas continuar?'
                );

                if (!confirmed) return;

                const result = await AuthService.enable2FA();
                if (result.success) {
                    button.dataset.enabled = 'true';
                    buttonText.textContent = 'Desactivar 2FA';
                    button.classList.replace('btn-outline-info', 'btn-outline-warning');
                    localStorage.setItem('two_factor_enabled', 'true');
                    alert('2FA activado correctamente. A partir de ahora necesitarás un código de verificación para iniciar sesión.');
                }
            } else {
                const confirmed = confirm('¿Estás seguro de que quieres desactivar la autenticación en dos pasos?');
                if (!confirmed) return;

                const result = await AuthService.disable2FA();
                if (result.success) {
                    button.dataset.enabled = 'false';
                    buttonText.textContent = 'Activar 2FA';
                    button.classList.replace('btn-outline-warning', 'btn-outline-info');
                    localStorage.removeItem('two_factor_enabled');
                    alert('2FA desactivado correctamente.');
                }
            }
        } catch (error) {
            alert(error.message);
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
}

async function loadUserData() {
    try {
        const userInfo = await AuthService.getUserProfile();
        console.log('UserInfo recibido:', userInfo);
        
        const profileImage = userInfo.profile_image || userInfo.fortytwo_image || 
                           `https://api.dicebear.com/7.x/avataaars/svg?seed=${userInfo.username}`;
        
        document.getElementById('userInfo').innerHTML = `
            <div class="text-center">
                <img src="${profileImage}" 
                     alt="avatar" 
                     class="rounded-circle profile-avatar mb-3" 
                     width="128"
                     height="128"
                     id="profileImage"
                     onerror="this.src='https://api.dicebear.com/7.x/avataaars/svg?seed=${userInfo.username}'">
                <h5 class="mb-2">${userInfo.username}</h5>
                <p class="text-muted mb-1">${userInfo.email}</p>
            </div>
        `;

        // Si es usuario de 42, ocultar campo de contraseña
        if (userInfo.is_fortytwo_user) {
            document.getElementById('deleteAccountPassword').parentElement.style.display = 'none';
        }

        // Actualizar detalles del perfil
        document.getElementById('profileUsername').textContent = userInfo.username;
        document.getElementById('profileEmail').textContent = userInfo.email;
        document.getElementById('profileStatus').innerHTML = `
            <span class="badge ${userInfo.is_active ? 'bg-success' : 'bg-warning'}">
                ${userInfo.is_active ? 'Activo' : 'Pendiente'}
            </span>
        `;

        // Actualizar estado del botón 2FA basado en el estado del servidor y localStorage
        const toggle2FABtn = document.getElementById('toggle2FABtn');
        const buttonText = document.getElementById('2faButtonText');
        const two_factor_enabled = localStorage.getItem('two_factor_enabled') === 'true';

        console.log('Estado 2FA actual:', { 
            from_server: userInfo.two_factor_enabled, 
            from_storage: two_factor_enabled 
        });

        if (two_factor_enabled) {
            console.log('2FA está activo, actualizando UI');
            toggle2FABtn.dataset.enabled = 'true';
            buttonText.textContent = 'Desactivar 2FA';
            toggle2FABtn.classList.remove('btn-outline-info');
            toggle2FABtn.classList.add('btn-outline-warning');
        } else {
            console.log('2FA está inactivo, actualizando UI');
            toggle2FABtn.dataset.enabled = 'false';
            buttonText.textContent = 'Activar 2FA';
            toggle2FABtn.classList.remove('btn-outline-warning');
            toggle2FABtn.classList.add('btn-outline-info');
        }

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
