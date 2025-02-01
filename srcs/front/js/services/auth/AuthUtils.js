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
        if (Array.isArray(backendMessage)) {
            backendMessage = backendMessage[0];
        }

        if (backendMessage.includes('Usuario o contraseña incorrectos')) {
            return {
                html: `
                    <div class="alert alert-danger fade show">
                        <i class="fas fa-user-lock fa-bounce"></i>
                        <div class="ms-2">
                            <h6 class="alert-heading mb-1">¡Acceso Denegado!</h6>
                            <span>${messages.AUTH.ERRORS.INVALID_CREDENTIALS}</span>
                        </div>
                    </div>
                `,
                message: messages.AUTH.ERRORS.INVALID_CREDENTIALS
            };
        }

        const errorStyles = {
            'Por favor verifica tu email': {
                icon: 'fas fa-envelope-circle-check fa-beat',
                message: messages.AUTH.ERRORS.EMAIL_NOT_VERIFIED,
                type: 'warning',
                title: '¡Falta un Paso!'
            },
            'No hay sesión activa': {
                icon: 'fas fa-hourglass-end fa-spin',
                message: messages.AUTH.ERRORS.NO_SESSION,
                type: 'warning',
                title: '¡Sesión Expirada!'
            },
            'default': {
                icon: 'fas fa-triangle-exclamation fa-shake',
                message: messages.AUTH.ERRORS.DEFAULT,
                type: 'danger',
                title: '¡Error!'
            }
        };

        const errorConfig = errorStyles[backendMessage] || errorStyles['default'];

        return {
            html: `
                <div class="alert alert-${errorConfig.type} fade show">
                    <i class="${errorConfig.icon}"></i>
                    <div class="ms-2">
                        <h6 class="alert-heading mb-1">${errorConfig.title}</h6>
                        <span>${errorConfig.message}</span>
                    </div>
                </div>
            `,
            message: errorConfig.message
        };
    }
}
