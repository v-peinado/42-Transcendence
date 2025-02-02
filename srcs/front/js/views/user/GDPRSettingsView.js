import AuthService from '../../services/AuthService.js';
import { loadHTML } from '../../utils/htmlLoader.js';

export async function GDPRSettingsView() {
    const app = document.getElementById('app');
    app.textContent = ''; // Limpiar de forma segura

    // Cargar el template
    const parser = new DOMParser();
    const html = await loadHTML('/views/user/gdpr/GDPRSettings.html');
    const content = parser.parseFromString(html, 'text/html').body.firstElementChild;
    app.appendChild(content);

    // Configurar manejadores de eventos
    setupEventHandlers();
    await loadGDPRSettings();
}

function setupEventHandlers() {
    const downloadBtn = document.getElementById('downloadData');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', async () => {
            try {
                const data = await AuthService.getGDPRSettings();
                downloadJSON(data, 'mis_datos_personales.json');
            } catch (error) {
                showMessage('Error al descargar datos: ' + error.message, 'danger');
            }
        });
    }

    // Nueva implementación del modal
    const deleteBtn = document.getElementById('deleteAccount');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', () => {
            const deleteModal = document.getElementById('deleteModal');
            if (deleteModal) {
                // Asegurarnos de que Bootstrap está disponible y cargar el modal
                if (typeof bootstrap !== 'undefined') {
                    // Crear nueva instancia del modal
                    new bootstrap.Modal(deleteModal).show();
                } else {
                    // Cargar Bootstrap si no está disponible
                    const script = document.createElement('script');
                    script.src = 'https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js';
                    script.onload = () => {
                        new bootstrap.Modal(deleteModal).show();
                    };
                    document.head.appendChild(script);
                }
            }
        });
    }

    // Manejar confirmación de eliminación
    const confirmDeleteBtn = document.getElementById('confirmDelete');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', async () => {
            const deleteModal = document.getElementById('deleteModal');
            const passwordInput = document.getElementById('deletePassword');
            
            if (!passwordInput?.value) {
                showMessage('Por favor, introduce tu contraseña', 'danger');
                return;
            }

            try {
                await AuthService.deleteAccount(passwordInput.value);
                if (typeof bootstrap !== 'undefined') {
                    const modalInstance = bootstrap.Modal.getInstance(deleteModal);
                    if (modalInstance) {
                        modalInstance.hide();
                    }
                }
                localStorage.clear();
                sessionStorage.clear();
                window.location.href = '/login';
            } catch (error) {
                showMessage(error.message || 'Error al eliminar la cuenta', 'danger');
            }
        });
    }
}

function downloadJSON(data, filename) {
    // Filtrar solo los datos relevantes del usuario
    const userData = {
        username: data.personal_info?.username,
        email: data.personal_info?.email,
        profile_image: data.personal_info?.profile_image,
        fortytwo_image: data.personal_info?.fortytwo_image,
        created_at: data.personal_info?.created_at,
        last_login: data.personal_info?.last_login,
        game_stats: data.game_stats || {},
        privacy_settings: {
            profile_public: data.personal_info?.profile_public,
            show_online_status: data.personal_info?.show_online_status,
            allow_game_invites: data.personal_info?.allow_game_invites
        }
    };

    const blob = new Blob([JSON.stringify(userData, null, 2)], {
        type: 'application/json'
    });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

async function loadGDPRSettings() {
    try {
        const data = await AuthService.getGDPRSettings();
        updateGDPRContent(data);
    } catch (error) {
        showMessage('Error al cargar configuración GDPR: ' + error.message, 'danger');
    }
}

function updateGDPRContent(data) {
    // Actualizar secciones de contenido
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

function showMessage(message, type) {
    const messageArea = document.getElementById('messageArea');
    if (messageArea) {
        messageArea.textContent = message;
        messageArea.className = `alert alert-${type} mt-3`;
        messageArea.classList.remove('d-none');
    }
}
