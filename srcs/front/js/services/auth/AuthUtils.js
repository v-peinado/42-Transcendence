import { messages } from '../../translations.js';

export class AuthUtils {
    static async clearSession(preserve2FA = false) {
        try {
            // Si queremos preservar 2FA, guardamos su estado
            const two_factor_enabled = preserve2FA ? 
                localStorage.getItem('two_factor_enabled') : 
                null;

            localStorage.clear();
            sessionStorage.clear();
            this.clearAllCookies();

            // Restauramos el estado de 2FA si es necesario
            if (preserve2FA && two_factor_enabled) {
                localStorage.setItem('two_factor_enabled', two_factor_enabled);
            }
        } catch (error) {
            console.error('Error limpiando sesión:', error);
        }
    }

    static clearAllCookies() {
        document.cookie.split(';').forEach(cookie => {
            const name = cookie.split('=')[0].trim();
            document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
            document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/api/;`;
        });
    }

    static getCSRFToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    static mapBackendError(backendMessage) {
        // En lugar de generar HTML, usaremos el template
        const template = document.getElementById('alertTemplate');
        if (!template) return { message: backendMessage };
        
        const alert = template.content.cloneNode(true);
        const message = this.getErrorConfig(backendMessage);
        
        alert.querySelector('.alert-heading').textContent = message.title;
        alert.querySelector('i').className = message.icon;
        alert.querySelector('span').textContent = message.message;
        
        return { html: alert.firstElementChild.outerHTML, message: message.message };
    }

    static getErrorConfig(backendMessage) {
        if (Array.isArray(backendMessage)) {
            backendMessage = backendMessage[0];
        }

        const errorTypes = {
            'Usuario o contraseña incorrectos': {
                icon: 'fas fa-user-lock fa-bounce',
                title: '¡Acceso Denegado!',
                message: messages.AUTH.ERRORS.INVALID_CREDENTIALS
            },
            'Por favor verifica tu email': {
                icon: 'fas fa-envelope-circle-check fa-beat',
                title: '¡Falta un Paso!',
                message: messages.AUTH.ERRORS.EMAIL_NOT_VERIFIED
            },
            'No hay sesión activa': {
                icon: 'fas fa-hourglass-end fa-spin',
                title: '¡Sesión Expirada!',
                message: messages.AUTH.ERRORS.NO_SESSION
            },
            'default': {
                icon: 'fas fa-triangle-exclamation fa-shake',
                title: '¡Error!',
                message: messages.AUTH.ERRORS.DEFAULT
            }
        };

        return errorTypes[backendMessage] || errorTypes['default'];
    }
}
