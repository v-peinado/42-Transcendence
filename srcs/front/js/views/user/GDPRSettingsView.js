import AuthService from '../../services/AuthService.js';
import { AuthGDPR } from '../../services/auth/AuthGDPR.js';
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
                await AuthGDPR.downloadUserData();
            } catch (error) {
                showMessage('Error al descargar datos: ' + error.message, 'danger');
            }
        });
    }
}

function downloadJSON(data, filename) {
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
        updateGDPRContent();
    } catch (error) {
        showMessage('Error al cargar configuración GDPR: ' + error.message, 'danger');
    }
}

function updateGDPRContent() {
    try {
        const gdprPolicy = AuthGDPR.getDefaultGDPRPolicy();
        
        const sections = {
            'data-collection': gdprPolicy.data_collection,
            'data-usage': gdprPolicy.data_usage,
            'user-rights': gdprPolicy.user_rights,
            'security-measures': gdprPolicy.security_measures,
            'data-retention': gdprPolicy.data_retention
        };

        Object.entries(sections).forEach(([id, items]) => {
            const element = document.getElementById(id);
            if (element && Array.isArray(items)) {
                element.innerHTML = items
                    .map(item => `<div class="mb-2"><i class="fas fa-check text-success me-2"></i>${item}</div>`)
                    .join('');
            }
        });
    } catch (error) {
        console.error('Error en updateGDPRContent:', error);
        showMessage('Error al actualizar contenido GDPR', 'danger');
    }
}

function showMessage(message, type) {
    const messageArea = document.getElementById('messageArea');
    if (messageArea) {
        messageArea.textContent = message;
        messageArea.className = `alert alert-${type} mt-3`;
        messageArea.classList.remove('d-none');
    }
}
