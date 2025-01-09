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
                                <label class="form-label">Nueva Contraseña (opcional)</label>
                                <input type="password" class="form-control" id="editPassword">
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                        <button type="button" class="btn btn-primary" id="saveProfileBtn">Guardar</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHTML);

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
            const newEmail = document.getElementById('editEmail').value;
            const currentEmail = document.getElementById('profileEmail').textContent;

            // Solo actualizamos si el email ha cambiado
            if (newEmail !== currentEmail) {
                const result = await AuthService.updateProfile({ email: newEmail });
                
                if (result.requiresVerification) {
                    const modalElement = document.getElementById('editProfileModal');
                    const modal = bootstrap.Modal.getInstance(modalElement);
                    
                    // Asegurarse de que el modal se cierre correctamente
                    modalElement.addEventListener('hidden.bs.modal', () => {
                        modalElement.remove(); // Eliminar el modal del DOM después de cerrarlo
                    }, { once: true });
                    
                    modal.hide();
                    
                    // Mostrar mensaje detallado
                    alert(`Se ha enviado un email de verificación a ${newEmail}. 
                          Por favor, revisa tu bandeja de entrada y sigue las instrucciones para confirmar el cambio. 
                          Mientras tanto, tu email actual seguirá siendo ${currentEmail}.`);
                }
            } else {
                alert('No has realizado ningún cambio en el email.');
            }
        } catch (error) {
            alert(error.message || 'Error al actualizar el perfil');
            console.error('Error al actualizar perfil:', error);
        }
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
