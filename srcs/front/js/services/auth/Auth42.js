import AuthService from '../AuthService.js';
import { messages } from '../../translations.js';

export class Auth42 {
    static async get42AuthUrl() {
        try {
            // Esta es la primera ruta de 42 (authentication/42/api/login/)
            const response = await fetch(`${AuthService.API_URL}/authentication/42/api/login/`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json'
                }
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.message || 'Error obteniendo URL de autenticación');
            }

            return data.auth_url;
        } catch (error) {
            console.error('Error obteniendo URL de 42:', error);
            throw error;
        }
    }

    static async handle42Callback(code) {
        try {
            console.log('Auth42: Enviando código a backend:', code);
            
            const response = await fetch(`${AuthService.API_URL}/authentication/42/api/callback/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': AuthService.getCSRFToken()
                },
                body: JSON.stringify({ code }),
                credentials: 'include'
            });

            const data = await response.json();
            console.log('Auth42: Respuesta del servidor:', data);

            // Manejar el nuevo formato de respuesta
            if (data.status === 'error' && data.message?.status === 'pending_verification') {
                return {
                    status: 'pending_verification',
                    message: data.message.message || messages.AUTH.EMAIL_VERIFICATION.MESSAGE
                };
            }

            // El resto de la lógica permanece igual
            if (data.require_2fa) {
                sessionStorage.setItem('pendingAuth', 'true');
                sessionStorage.setItem('fortytwo_user', 'true');
                return {
                    status: 'pending_2fa',
                    username: data.username,
                    message: 'Se requiere verificación en dos pasos'
                };
            }

            if (data.status === 'success') {
                localStorage.setItem('isAuthenticated', 'true');
                localStorage.setItem('username', data.username);
                window.location.replace('/');
                return { 
                    status: 'success',
                    username: data.username
                };
            }

            throw new Error(data.message?.message || data.message || messages.AUTH.ERRORS.LOGIN_FAILED);
        } catch (error) {
            console.error('Auth42: Error detallado:', error);
            throw error;
        }
    }

    static async handleFortyTwoCallback(code) {
        try {
            // Esta es la segunda ruta de callback (auth/42/callback)
            const response = await fetch(`${AuthService.API_URL}/auth/42/callback`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ code })
            });

            const data = await response.json();

            if (data.require_2fa) {
                sessionStorage.setItem('pendingAuth', 'true');
                sessionStorage.setItem('fortytwo_user', 'true');
                return { requireTwoFactor: true };
            }

            if (data.status === 'success') {
                localStorage.setItem('isAuthenticated', 'true');
                localStorage.setItem('username', data.username);
                window.location.replace('/'); // Cambiado de '/profile' a '/'
                return { success: true };
            }

            throw new Error(data.message);
        } catch (error) {
            throw new Error(error.message || 'Error en la autenticación con 42');
        }
    }
}
