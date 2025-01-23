import AuthService from '../../services/AuthService.js';

// Vista ya implementada que maneja:
// - Mostrar política de privacidad
// - Mostrar y actualizar configuraciones GDPR
// - Manejo de errores y mensajes

export function GDPRSettingsView() {
    const app = document.getElementById('app');
    app.innerHTML = `
        <div class="container py-4">
            <div class="row justify-content-center">
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-center mb-4">
                                <h3 class="card-title mb-0">Política de Privacidad</h3>
                                <a href="/profile" data-link class="btn btn-outline-secondary btn-sm">
                                    <i class="fas fa-arrow-left me-2"></i>Volver
                                </a>
                            </div>
                            
                            <!-- Secciones de GDPR -->
                            <div class="mb-4">
                                <h5><i class="fas fa-database me-2"></i>Recopilación de Datos</h5>
                                <div id="data-collection" class="ps-4 text-muted"></div>
                            </div>

                            <div class="mb-4">
                                <h5><i class="fas fa-tasks me-2"></i>Uso de Datos</h5>
                                <div id="data-usage" class="ps-4 text-muted"></div>
                            </div>

                            <div class="mb-4">
                                <h5><i class="fas fa-user-shield me-2"></i>Tus Derechos</h5>
                                <div id="user-rights" class="ps-4 text-muted"></div>
                            </div>

                            <div class="mb-4">
                                <h5><i class="fas fa-lock me-2"></i>Medidas de Seguridad</h5>
                                <div id="security-measures" class="ps-4 text-muted"></div>
                            </div>

                            <form id="gdprForm">
                                <div class="mb-4">
                                    <div class="form-check form-switch">
                                        <label class="form-check-label" for="profilePublic">
                                            Perfil público
                                        </label>
                                        <small class="text-muted d-block">
                                            Tu perfil y estadísticas serán visibles para otros usuarios
                                        </small>
                                    </div>
                                </div>

                                <div class="mb-4">
                                    <div class="form-check form-switch">
                                        <label class="form-check-label" for="showOnlineStatus">
                                            Mostrar estado en línea
                                        </label>
                                        <small class="text-muted d-block">
                                            Otros usuarios podrán ver cuando estás conectado
                                        </small>
                                    </div>
                                </div>

                                <div class="mb-4">
                                    <div class="form-check form-switch">
                                        <label class="form-check-label" for="allowGameInvites">
                                            Permitir invitaciones a partidas
                                        </label>
                                        <small class="text-muted d-block">
                                            Otros jugadores podrán invitarte a jugar
                                        </small>
                                    </div>
                                </div>
                            </form>

                            <div class="mt-4 border-top pt-4">
                                <h4><i class="fas fa-download me-2"></i>Exportar Datos</h4>
                                <p class="text-muted">Descarga todos tus datos personales en formato JSON</p>
                                <button id="downloadData" class="btn btn-secondary">
                                    <i class="fas fa-file-download me-2"></i>Descargar mis datos
                                </button>
                            </div>

                            <div class="mt-4 border-top pt-4">
                                <h4 class="text-danger"><i class="fas fa-exclamation-triangle me-2"></i>Eliminar Cuenta</h4>
                                <p class="text-muted">Esta acción es irreversible. Todos tus datos serán eliminados permanentemente.</p>
                                <button id="deleteAccount" class="btn btn-danger">
                                    <i class="fas fa-user-times me-2"></i>Eliminar mi cuenta
                                </button>
                            </div>

                            <!-- Modal de confirmación -->
                            <div class="modal fade" id="deleteModal" tabindex="-1">
                                <div class="modal-dialog">
                                    <div class="modal-content">
                                        <div class="modal-header">
                                            <h5 class="modal-title">Confirmar eliminación</h5>
                                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                        </div>
                                        <div class="modal-body">
                                            <p>Por favor, ingresa tu contraseña para confirmar la eliminación de tu cuenta:</p>
                                            <input type="password" id="deletePassword" class="form-control" placeholder="Contraseña">
                                        </div>
                                        <div class="modal-footer">
                                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                                            <button type="button" class="btn btn-danger" id="confirmDelete">Eliminar</button>
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

    loadGDPRSettings();
    setupFormHandler();

    // Agregar manejadores para nuevas funciones
    document.getElementById('downloadData').addEventListener('click', async () => {
        try {
            await AuthService.downloadUserData();
        } catch (error) {
            showMessage('Error al descargar datos: ' + error.message, 'danger');
        }
    });

    document.getElementById('deleteAccount').addEventListener('click', () => {
        const deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));
        deleteModal.show();
    });

    document.getElementById('confirmDelete').addEventListener('click', async () => {
        const password = document.getElementById('deletePassword').value;
        try {
            await AuthService.deleteAccount(password);
            localStorage.clear();
            window.location.href = '/login';
        } catch (error) {
            showMessage(error.message, 'danger');
        }
    });
}

async function loadGDPRSettings() {
    try {
        const data = await AuthService.getGDPRSettings();
        
        // Actualizar checkboxes usando los nombres correctos
        document.getElementById('profilePublic').checked = data.personal_info?.profile_public || false;
        document.getElementById('showOnlineStatus').checked = data.personal_info?.show_online_status || false;
        document.getElementById('allowGameInvites').checked = data.personal_info?.allow_game_invites || false;

        // Actualizar secciones de la política de privacidad
        if (data.data_collection) {
            document.getElementById('data-collection').innerHTML = 
                data.data_collection.map(item => `<div class="mb-2">${item}</div>`).join('');
        }
        if (data.data_usage) {
            document.getElementById('data-usage').innerHTML = 
                data.data_usage.map(item => `<div class="mb-2">${item}</div>`).join('');
        }
        if (data.user_rights) {
            document.getElementById('user-rights').innerHTML = 
                data.user_rights.map(item => `<div class="mb-2">${item}</div>`).join('');
        }
        if (data.security_measures) {
            document.getElementById('security-measures').innerHTML = 
                data.security_measures.map(item => `<div class="mb-2">${item}</div>`).join('');
        }
    } catch (error) {
        showMessage('Error al cargar las preferencias: ' + error.message, 'danger');
    }
}

function setupFormHandler() {
    document.getElementById('gdprForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const settings = {
            personal_info: {
                username: document.getElementById('profilePublic').checked,
                email: document.getElementById('showOnlineStatus').checked
            },
            security_settings: {
                two_factor_enabled: document.getElementById('allowGameInvites').checked
            }
        };

        try {
            const result = await AuthService.updateGDPRSettings(settings);
            if (result.status === 'success') {
                showMessage('Preferencias actualizadas correctamente', 'success');
            } else {
                showMessage(result.message || 'Error al actualizar las preferencias', 'danger');
            }
        } catch (error) {
            showMessage(error.message || 'Error al actualizar las preferencias', 'danger');
        }
    });
}

function showMessage(message, type) {
    const messageArea = document.getElementById('messageArea');
    messageArea.textContent = message;
    messageArea.className = `alert alert-${type}`;
    messageArea.classList.remove('d-none');
}
