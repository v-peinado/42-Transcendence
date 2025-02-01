import AuthService from '../AuthService.js';

export class AuthGDPR {
    static async getGDPRSettings() {
        try {
            // Obtener política de privacidad
            const policyResponse = await fetch(`${AuthService.API_URL}/gdpr/privacy-policy/`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'X-CSRFToken': AuthService.getCSRFToken()
                },
                credentials: 'include'
            });

            // Obtener datos personales
            const dataResponse = await fetch(`${AuthService.API_URL}/gdpr/export-data/`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'X-CSRFToken': AuthService.getCSRFToken()
                },
                credentials: 'include'
            });

            if (!policyResponse.ok || !dataResponse.ok) {
                throw new Error('Error al obtener datos GDPR');
            }

            const policy = await policyResponse.json();
            const userData = await dataResponse.json();

            return {
                ...policy.data,
                ...userData.data
            };
        } catch (error) {
            throw error;
        }
    }

    static async updateGDPRSettings(settings) {
        try {
            const response = await fetch(`${AuthService.API_URL}/gdpr/data/`, {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'X-CSRFToken': AuthService.getCSRFToken()
                },
                body: JSON.stringify({
                    settings: {
                        profile_public: settings.personal_info.username,
                        show_online_status: settings.personal_info.email,
                        allow_game_invites: settings.security_settings.two_factor_enabled
                    }
                }),
                credentials: 'include'
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.message || 'Error al actualizar configuraciones');
            }

            return await response.json();
        } catch (error) {
            throw error;
        }
    }

    static async downloadUserData() {
        try {
            const response = await fetch(`${AuthService.API_URL}/gdpr/export-data/`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'X-CSRFToken': AuthService.getCSRFToken()
                },
                credentials: 'include'
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.message || 'Error al descargar datos');
            }

            const data = await response.json();
            
            // Crear archivo de descarga
            const blob = new Blob([JSON.stringify(data.data, null, 2)], {
                type: 'application/json'
            });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'mis_datos.json';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        } catch (error) {
            throw error;
        }
    }
}
