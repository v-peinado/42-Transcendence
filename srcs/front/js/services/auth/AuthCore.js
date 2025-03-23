import AuthService from '../AuthService.js';
import { AuthUtils } from './AuthUtils.js';
import { messages } from '../../translations.js';
import RateLimitService from '../RateLimitService.js';

export class AuthCore {
    static async login(username, password, remember = false) {
        try {
            await AuthUtils.clearSession();
            await new Promise(resolve => setTimeout(resolve, 100));
            
            const response = await fetch(`${AuthService.API_URL}/login/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': AuthUtils.getCSRFToken()
                },
                body: JSON.stringify({ username, password, remember }),
                credentials: 'include'
            });

            const responseText = await response.text();
            let data;
            
            try {
                data = JSON.parse(responseText);
                console.log('Login response:', data);

                if (!response.ok) {
                    // Caso específico de rate limit
                    if (response.status === 429 || data.status === 'rate_limit') {
                        const seconds = data.remaining_time || data.message?.match(/\d+/)?.[0] || 900;
                        return RateLimitService.getMessage('login', parseInt(seconds));
                    }

                    // Procesar error de credenciales incorrectas
                    if (data.status === 'error' && data.message === "['Incorrect username or password']") {
                        throw new Error(messages.AUTH.ERRORS.INVALID_CREDENTIALS);
                    }

                    // Si no es un error específico, lanzar el error completo
                    throw new Error(JSON.stringify(data));
                }

                if (data.status === 'pending_2fa') {
                    return { 
                        status: 'pending_2fa',
                        message: data.message || 'Se requiere verificación en dos pasos'
                    };
                }
                
                if (data.status === 'success') {
                    localStorage.setItem('isAuthenticated', 'true');
                    localStorage.setItem('username', username);
                    
                    if (data.user_id) {
                        localStorage.setItem('user_id', data.user_id.toString());
                    }
                    
                    if (data.two_factor_enabled) {
                        localStorage.setItem('two_factor_enabled', 'true');
                    }

                    return {
                        status: 'success',
                        message: 'Login exitoso',
                        username: data.username,
                        redirect: '/game', // Forzar redirección a /game independientemente de la respuesta
                        require_2fa: data.require_2fa
                    };
                }

                throw new Error(AuthUtils.mapBackendError('default').html);
            } catch (e) {
                // Manejo específico para respuestas de texto plano con rate limit
                if (responseText.includes('Too many attempts') || responseText.includes('Demasiados intentos')) {
                    const match = responseText.match(/(\d+)/);
                    const seconds = match ? parseInt(match[1]) : 900;
                    
                    return RateLimitService.getMessage('login', seconds);
                }
                throw new Error(responseText);
            }
        } catch (error) {
            console.log('Login error caught:', error);
            
            // Verificar si es un error de rate limit
            if (error.response?.status === 429 || error.message?.includes('Too many attempts')) {
                const seconds = error.response?.data?.remaining_time || 900;
                return RateLimitService.getMessage('login', seconds);
            }

            // Verificar si es un error de rate limit de envío de email
            if (error.message?.includes("Demasiados intentos") && error.message?.includes("segundos")) {
                const seconds = parseInt(error.message.match(/\d+/)[0]);
                return RateLimitService.getMessage('email_send', seconds);
            }

            throw error;
        }
    }

    formatErrorMessage(message) {
        return `
            <div class="alert alert-danger fade show d-flex align-items-center">
                <i class="fas fa-triangle-exclamation fa-shake"></i>
                <div class="ms-2">
                    <h6 class="alert-heading mb-1">¡Error!</h6>
                    <span>${message}</span>
                </div>
            </div>
        `;
    }

    static async logout() {
        try {
            const response = await fetch(`${AuthService.API_URL}/logout/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': AuthUtils.getCSRFToken()
                },
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error('Error en el logout');
            }

            // Guardar el estado de 2FA antes de limpiar
            const two_factor_enabled = localStorage.getItem('two_factor_enabled');
            
            // Limpiar todo excepto 2FA
            await AuthUtils.clearSession(true);
            
            // Restaurar el estado de 2FA
            if (two_factor_enabled) {
                localStorage.setItem('two_factor_enabled', two_factor_enabled);
            }

            return { success: true };
        } catch (error) {
            console.error('Error en logout:', error);
            await AuthUtils.clearSession();
            throw error;
        }
    }
}

export default new AuthCore();
