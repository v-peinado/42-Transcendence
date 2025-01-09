import AuthService from '../../services/AuthService.js';

export function UserProfileView() {
    const app = document.getElementById('app');
    app.innerHTML = `
        <div class="profile-section">
            <div class="container py-4">
                <div class="row g-3">
                    <!-- Perfil Card Compacto -->
                    <div class="col-lg-4">
                        <div class="card profile-card h-100">
                            <div class="card-body p-3">
                                <div class="text-center">
                                    <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=default" 
                                         alt="avatar" class="rounded-circle profile-avatar" width="100">
                                    <div class="mt-2" id="userInfo">
                                        <div class="placeholder-glow">
                                            <span class="placeholder col-6"></span>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Stats Grid -->
                                <div class="row g-2 mt-3 text-center">
                                    <div class="col-4">
                                        <div class="stats-badge">
                                            <i class="fas fa-trophy text-warning"></i>
                                            <div class="mt-1">25</div>
                                            <small>Victorias</small>
                                        </div>
                                    </div>
                                    <div class="col-4">
                                        <div class="stats-badge">
                                            <i class="fas fa-gamepad text-primary"></i>
                                            <div class="mt-1">42</div>
                                            <small>Partidas</small>
                                        </div>
                                    </div>
                                    <div class="col-4">
                                        <div class="stats-badge">
                                            <i class="fas fa-star text-info"></i>
                                            <div class="mt-1">8</div>
                                            <small>Nivel</small>
                                        </div>
                                    </div>
                                </div>

                                <!-- Action Buttons -->
                                <div class="d-flex gap-2 mt-3">
                                    <button class="btn btn-primary flex-grow-1">
                                        <i class="fas fa-gamepad me-2"></i>Jugar
                                    </button>
                                    <button id="editProfileBtn" class="btn btn-outline-light">
                                        <i class="fas fa-cog"></i>
                                    </button>
                                    <button id="logoutBtn" class="btn btn-outline-danger">
                                        <i class="fas fa-sign-out-alt"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Info y Historial -->
                    <div class="col-lg-8">
                        <div class="row g-3">
                            <!-- Info Card -->
                            <div class="col-12">
                                <div class="card profile-card">
                                    <div class="card-body p-3">
                                        <div class="d-flex justify-content-between align-items-center mb-2">
                                            <div>
                                                <small class="text-muted">Username</small>
                                                <div id="profileUsername">Cargando...</div>
                                            </div>
                                            <div>
                                                <small class="text-muted">Email</small>
                                                <div id="profileEmail">Cargando...</div>
                                            </div>
                                            <div>
                                                <small class="text-muted">Estado</small>
                                                <div id="profileStatus">
                                                    <span class="badge bg-secondary">Cargando...</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Match History Card -->
                            <div class="col-12">
                                <div class="card match-history">
                                    <div class="card-body p-3">
                                        <h6 class="text-light mb-3">
                                            <i class="fas fa-history me-2"></i>Últimas Partidas
                                        </h6>
                                        <div class="table-responsive" style="max-height: 200px;">
                                            <table class="table table-sm table-hover mb-0">
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
                                                        <td>Player123</td>
                                                        <td><span class="badge bg-success">Victoria</span></td>
                                                        <td>10-8</td>
                                                    </tr>
                                                    <tr>
                                                        <td>2024-01-19</td>
                                                        <td>GameMaster</td>
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
}

function setupProfileEvents() {
    // Agregar el event listener para logout
    document.getElementById('logoutBtn')?.addEventListener('click', async () => {
        try {
            await AuthService.logout();
            localStorage.removeItem('isAuthenticated');
            localStorage.removeItem('username');
            window.location.href = '/login';
        } catch (error) {
            console.error('Error en logout:', error);
            alert('Error al cerrar sesión');
        }
    });

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
}

async function loadUserData() {
    try {
        const userInfo = await AuthService.getUserProfile();
        
        // Forzar recarga de datos desde el servidor sin caché
        const freshUserInfo = await AuthService.getUserProfile({ cache: 'no-store' });
        
        // Actualizar información del usuario
        document.getElementById('userInfo').innerHTML = `
            <h5 class="my-3">${freshUserInfo.username}</h5>
            <p class="text-muted mb-1">${freshUserInfo.email}</p>
        `;

        // Actualizar detalles del perfil
        document.getElementById('profileUsername').textContent = freshUserInfo.username;
        document.getElementById('profileEmail').textContent = freshUserInfo.email;
        document.getElementById('profileStatus').innerHTML = `
            <span class="badge ${freshUserInfo.is_active ? 'bg-success' : 'bg-warning'}">
                ${freshUserInfo.is_active ? 'Activo' : 'Pendiente'}
            </span>
        `;

    } catch (error) {
        console.error('Error cargando datos:', error);
    }
}
