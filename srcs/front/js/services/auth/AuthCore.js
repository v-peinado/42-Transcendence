import AuthService from '../AuthService.js';
import { AuthUtils } from './AuthUtils.js';
import { messages } from '../../translations.js';
import RateLimitService from '../RateLimitService.js';

export class AuthCore {
    static async login(username, password, remember = false) {
        try {
            // Limpiar completamente cualquier estado previo
            await AuthUtils.clearSession();
            
            // Esperar un momento para asegurar que todo está limpio
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

            let responseText;
            try {
                // Primero guardamos el texto de la respuesta
                responseText = await response.text();
                
                // Intentamos parsear como JSON
                const data = JSON.parse(responseText);
                console.log('Login response:', data);

                if (!response.ok) {
                    // Manejar rate limit
                    if (responseText.includes('Demasiados intentos')) {
                        const match = responseText.match(/(\d+) segundos/);
                        if (match) {
                            const seconds = parseInt(match[1]);
                            const formattedTime = RateLimitService.formatTimeRemaining(seconds);
                            
                            return {
                                status: 'rate_limit',
                                remaining_time: seconds,
                                title: messages.AUTH.RATE_LIMIT.TITLE,
                                message: messages.AUTH.RATE_LIMIT.MESSAGES.login.replace('{time}', formattedTime)
                            };
                        }
                    }

                    // Manejar credenciales incorrectas
                    if (data.message?.[0] === 'Incorrect username or password') {
                        throw new Error(messages.AUTH.ERRORS.INVALID_CREDENTIALS);
                    }

                    // Otros errores
                    const errorMessage = Array.isArray(data.message) 
                        ? data.message[0] 
                        : (data.message || messages.AUTH.ERRORS.DEFAULT);
                    throw new Error(errorMessage);
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
                    
                    // Solo añadir esta línea para el ID de usuario
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
                        redirect: '/',
                        require_2fa: data.require_2fa
                    };
                }

                throw new Error(AuthUtils.mapBackendError('default').html);
            } catch (e) {
                // Si no es JSON válido pero contiene el mensaje de rate limit
                if (responseText.includes('Demasiados intentos')) {
                    const match = responseText.match(/(\d+) segundos/);
                    if (match) {
                        const seconds = parseInt(match[1]);
                        const formattedTime = RateLimitService.formatTimeRemaining(seconds);
                        
                        return {
                            status: 'rate_limit',
                            remaining_time: seconds,
                            title: messages.AUTH.RATE_LIMIT.TITLE,
                            message: messages.AUTH.RATE_LIMIT.MESSAGES.login.replace('{time}', formattedTime)
                        };
                    }
                }
                throw new Error(responseText);
            }
        } catch (error) {
            console.log('Login error caught:', error); // Debug log
            
            // Si ya es un objeto rate_limit, retornarlo directamente
            if (error.status === 'rate_limit') {
                return error;
            }
            
            // Si el error contiene el mensaje de rate limit, procesarlo
            if (typeof error.message === 'string' && error.message.includes('Too many attempts')) {
                const seconds = parseInt(error.message.match(/\d+/)[0]);
                const formattedTime = RateLimitService.formatTimeRemaining(seconds);
                
                return {
                    status: 'rate_limit',
                    remaining_time: seconds,
                    title: messages.AUTH.RATE_LIMIT.TITLE,
                    message: messages.AUTH.RATE_LIMIT.LOGIN_MESSAGE.replace('{time}', formattedTime)
                };
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
