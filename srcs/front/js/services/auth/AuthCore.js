import AuthService from '../AuthService.js';
import { AuthUtils } from './AuthUtils.js';
import { messages } from '../../translations.js';

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
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(AuthUtils.mapBackendError(data.message || 'default').html);
            }

            if (data.status === 'pending_2fa') {
                return { 
                    status: 'pending_2fa',
                    message: data.message || 'Se requiere verificación en dos pasos'
                };
            }
            
            if (data.status === 'success') {
                // Guardar sessionId después del login
                const cookies = document.cookie.split(';').reduce((acc, cookie) => {
                    const [name, value] = cookie.trim().split('=');
                    acc[name] = value;
                    return acc;
                }, {});

                console.log('Login exitoso - Cookies:', cookies);

                if (cookies.sessionid) {
                    localStorage.setItem('sessionid', cookies.sessionid);
                    console.log('SessionID guardada:', cookies.sessionid);
                }

                localStorage.setItem('isAuthenticated', 'true');
                localStorage.setItem('username', username);
                
                // Añadir esta línea para guardar el estado del 2FA
                if (data.two_factor_enabled) {
                    localStorage.setItem('two_factor_enabled', 'true');
                }

                // Guardar el user_id si viene en la respuesta
                if (data.user_id) {
                    localStorage.setItem('user_id', data.user_id);
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
        } catch (error) {
            if (!error.message.includes('alert')) {
                throw new Error(AuthUtils.mapBackendError('default').html);
            }
            throw error;
        }
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
