import AuthService from '../../services/AuthService.js';

export function GDPRSettingsView() {
    const app = document.getElementById('app');
    app.innerHTML = `
        <main class="profile-section">
            <div class="container py-4">
                <div class="row justify-content-center">
                    <div class="col-md-8">
                        <div class="card bg-dark text-light border-0 shadow">
                            <div class="card-body p-4">
                                <div class="d-flex justify-content-between align-items-center mb-4">
                                    <div class="d-flex align-items-center">
                                        <div class="icon-square bg-primary me-3">
                                            <i class="fas fa-shield-alt fs-2"></i>
                                        </div>
                                        <h3 class="card-title mb-0">Privacidad y Seguridad</h3>
                                    </div>
                                    <a href="/profile" data-link class="btn btn-outline-light btn-sm">
                                        <i class="fas fa-arrow-left me-2"></i>Volver
                                    </a>
                                </div>
                                
                                <!-- Secciones de GDPR con iconos y efectos -->
                                <div class="gdpr-section mb-4">
                                    <div class="section-header" role="button" data-bs-toggle="collapse" data-bs-target="#dataCollectionContent">
                                        <i class="fas fa-database text-primary me-2"></i>
                                        <h5 class="mb-0">Recopilación de Datos</h5>
                                        <i class="fas fa-chevron-down ms-auto transition-transform"></i>
                                    </div>
                                    <div class="collapse show" id="dataCollectionContent">
                                        <div class="p-3 mt-2 section-explanation bg-dark-subtle rounded">
                                            <p>Los siguientes datos son necesarios para proporcionar nuestros servicios:</p>
                                        </div>
                                        <div id="data-collection" class="ps-4 text-muted section-content mt-3"></div>
                                    </div>
                                </div>

                                <div class="gdpr-section mb-4">
                                    <div class="section-header" role="button" data-bs-toggle="collapse" data-bs-target="#dataUsageContent">
                                        <i class="fas fa-tasks text-info me-2"></i>
                                        <h5 class="mb-0">Uso de Datos</h5>
                                        <i class="fas fa-chevron-down ms-auto transition-transform"></i>
                                    </div>
                                    <div class="collapse" id="dataUsageContent">
                                        <div class="p-3 mt-2 section-explanation bg-dark-subtle rounded">
                                            <p>Utilizamos tus datos de las siguientes maneras:</p>
                                        </div>
                                        <div id="data-usage" class="ps-4 text-muted section-content mt-3"></div>
                                    </div>
                                </div>

                                <div class="gdpr-section mb-4">
                                    <div class="section-header" role="button" data-bs-toggle="collapse" data-bs-target="#userRightsContent">
                                        <i class="fas fa-user-shield text-success me-2"></i>
                                        <h5 class="mb-0">Tus Derechos</h5>
                                        <i class="fas fa-chevron-down ms-auto transition-transform"></i>
                                    </div>
                                    <div class="collapse" id="userRightsContent">
                                        <div class="p-3 mt-2 section-explanation bg-dark-subtle rounded">
                                            <p>Como usuario, tienes los siguientes derechos sobre tus datos:</p>
                                        </div>
                                        <div id="user-rights" class="ps-4 text-muted section-content mt-3"></div>
                                    </div>
                                </div>

                                <div class="gdpr-section mb-4">
                                    <div class="section-header" role="button" data-bs-toggle="collapse" data-bs-target="#securityContent">
                                        <i class="fas fa-lock text-warning me-2"></i>
                                        <h5 class="mb-0">Medidas de Seguridad</h5>
                                        <i class="fas fa-chevron-down ms-auto transition-transform"></i>
                                    </div>
                                    <div class="collapse" id="securityContent">
                                        <div class="p-3 mt-2 section-explanation bg-dark-subtle rounded">
                                            <p>Implementamos las siguientes medidas para proteger tus datos:</p>
                                        </div>
                                        <div id="security-measures" class="ps-4 text-muted section-content mt-3"></div>
                                    </div>
                                </div>
                                        </div>
                                    </form>
                                </div>

                                <!-- Acciones con botones más atractivos -->
                                <div class="actions-section mt-5">
                                    <div class="row g-4">
                                        <div class="col-md-6">
                                            <div class="action-card bg-info bg-opacity-10 p-4 rounded">
                                                <h5><i class="fas fa-download text-info me-2"></i>Exportar Datos</h5>
                                                <p class="text-muted mb-3">Descarga todos tus datos personales en formato JSON</p>
                                                <button id="downloadData" class="btn btn-info">
                                                    <i class="fas fa-file-download me-2"></i>Descargar
                                                </button>
                                            </div>
                                        </div>
                                        <div class="col-md-6">
                                            <div class="action-card bg-danger bg-opacity-10 p-4 rounded">
                                                <h5><i class="fas fa-exclamation-triangle text-danger me-2"></i>Zona de Peligro</h5>
                                                <p class="text-muted mb-3">Esta acción eliminará permanentemente tu cuenta</p>
                                                <button id="deleteAccount" class="btn btn-danger">
                                                    <i class="fas fa-user-times me-2"></i>Eliminar Cuenta
                                                </button>
                                            </div>
                                        </div>
                                    </div>
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
        </main>
    `;

    loadGDPRSettings();
    setupFormHandler();

    // Agregar manejadores para nuevas funciones
    document.getElementById('downloadData').addEventListener('click', async () => {
        try {
            const data = await AuthService.getGDPRSettings();
            
            // Crear archivo de descarga
            const blob = new Blob([JSON.stringify(data, null, 2)], {
                type: 'application/json'
            });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'mis_datos_personales.json';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
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

        // Actualizar el contenido de GDPR directamente desde la API
        document.getElementById('data-collection').innerHTML = data.gdpr_policy.data_collection
            .map(item => `<div class="mb-2">${item}</div>`).join('');

        document.getElementById('data-usage').innerHTML = data.gdpr_policy.data_usage
            .map(item => `<div class="mb-2">${item}</div>`).join('');

        document.getElementById('user-rights').innerHTML = data.gdpr_policy.user_rights
            .map(item => `<div class="mb-2">${item}</div>`).join('');

        document.getElementById('security-measures').innerHTML = data.gdpr_policy.security_measures
            .map(item => `<div class="mb-2">${item}</div>`).join('');
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
