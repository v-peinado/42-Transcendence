import AuthService from '../AuthService.js';
import RateLimitService from '../RateLimitService.js';
import { messages } from '../../translations.js';

export class Auth2FA {
    static get isEnabled() {
        return localStorage.getItem('two_factor_enabled') === 'true';
    }

    static set isEnabled(value) {
        if (value) {
            localStorage.setItem('two_factor_enabled', 'true');
        } else {
            localStorage.removeItem('two_factor_enabled');
        }
        
        // Actualizar UI si existe
        const toggle2FABtn = document.getElementById('toggle2FABtn');
        const buttonText = document.getElementById('2faButtonText');
        if (toggle2FABtn && buttonText) {
            toggle2FABtn.dataset.enabled = value.toString();
            buttonText.textContent = value ? 'Desactivar 2FA' : 'Activar 2FA';
            toggle2FABtn.classList.remove('btn-outline-info', 'btn-outline-warning');
            toggle2FABtn.classList.add(value ? 'btn-outline-warning' : 'btn-outline-info');
        }
    }

    static async enable2FA() {
        try {
            const response = await fetch(`${AuthService.API_URL}/enable-2fa/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': AuthService.getCSRFToken()
                },
                credentials: 'include'
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || 'Error al activar 2FA');
            }

            this.isEnabled = true;
            return {
                success: true,
                ...data
            };
        } catch (error) {
            throw error;
        }
    }

    static async disable2FA() {
        try {
            const response = await fetch(`${AuthService.API_URL}/disable-2fa/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': AuthService.getCSRFToken()
                },
                credentials: 'include'
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || 'Error al desactivar 2FA');
            }

            this.isEnabled = false;
            return {
                success: true,
                ...data
            };
        } catch (error) {
            throw error;
        }
    }

    static async verify2FACode(code, isFortytwoUser = false) {
        try {
            console.log('Verificando código 2FA:', { code, isFortytwoUser });
            
            const endpoint = isFortytwoUser ? 
                `${AuthService.API_URL}/auth/42/verify-2fa/` :
                `${AuthService.API_URL}/verify-2fa/`;
            
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': AuthService.getCSRFToken()
                },
                body: JSON.stringify({ code }),
                credentials: 'include'
            });

            let data;
            try {
                data = await response.json();
            } catch (e) {
                const text = await response.text();
                
                // Verificar si es un error de rate limit
                if (text.includes('Demasiados intentos')) {
                    const match = text.match(/(\d+) segundos/);
                    if (match) {
                        const seconds = parseInt(match[1]);
                        const formattedTime = RateLimitService.formatTimeRemaining(seconds);
                        
                        return {
                            status: 'rate_limit',
                            remaining_time: seconds,
                            title: messages.AUTH.RATE_LIMIT.TITLE,
                            message: messages.AUTH.RATE_LIMIT.MESSAGES.two_factor.replace('{time}', formattedTime)
                        };
                    }
                }
                throw new Error(text);
            }

            console.log('2FA response:', data);

            if (!response.ok) {
                // Detectar rate limit por el mensaje
                if (data.message && Array.isArray(data.message)) {
                    const msg = data.message[0];
                    if (msg.includes('Too many attempts')) {
                        const seconds = parseInt(msg.match(/\d+/)[0]);
                        const formattedTime = RateLimitService.formatTimeRemaining(seconds);
                        
                        return {
                            status: 'rate_limit',
                            remaining_time: seconds,
                            title: messages.AUTH.RATE_LIMIT.TITLE,
                            message: messages.AUTH.RATE_LIMIT.MESSAGES.two_factor.replace('{time}', formattedTime)
                        };
                    }
                }
                throw new Error(data.message || 'Error en la verificación');
            }

            if (data.status === 'success') {
                localStorage.setItem('isAuthenticated', 'true');
                if (data.username) {
                    localStorage.setItem('username', data.username);
                }
                // Añadir esta línea para asegurar que el estado del 2FA se mantiene
                localStorage.setItem('two_factor_enabled', 'true');
                return {
                    status: 'success',
                    username: data.username || sessionStorage.getItem('pendingUsername'),
                    redirect: '/profile'
                };
            }

            return data;
        } catch (error) {
            console.error('2FA error details:', error);
            
            // Verificar si el mensaje de error contiene información de rate limit
            if (error.message && error.message.includes('Demasiados intentos')) {
                const match = error.message.match(/(\d+) segundos/);
                if (match) {
                    const seconds = parseInt(match[1]);
                    const formattedTime = RateLimitService.formatTimeRemaining(seconds);
                    
                    return {
                        status: 'rate_limit',
                        remaining_time: seconds,
                        title: messages.AUTH.RATE_LIMIT.TITLE,
                        message: messages.AUTH.RATE_LIMIT.MESSAGES.two_factor.replace('{time}', formattedTime)
                    };
                }
            }

            // Si el error ya viene formateado como rate limit, devolverlo
            if (error.status === 'rate_limit') {
                return error;
            }

            // Si el mensaje contiene "Too many attempts", procesarlo
            if (typeof error.message === 'string' && error.message.includes('Too many attempts')) {
                const seconds = parseInt(error.message.match(/\d+/)[0]);
                const formattedTime = RateLimitService.formatTimeRemaining(seconds);
                
                return {
                    status: 'rate_limit',
                    remaining_time: seconds,
                    title: messages.AUTH.RATE_LIMIT.TITLE,
                    message: messages.AUTH.RATE_LIMIT.MESSAGES.two_factor.replace('{time}', formattedTime)
                };
            }

            throw error;
        }
    }

    static async generateQR(username) {
        try {
            const response = await fetch(`${AuthService.API_URL}/generate-qr/${username}/`, {
                method: 'GET',
                headers: {
                    'Accept': '*/*',
                    'X-CSRFToken': AuthService.getCSRFToken()
                },
                credentials: 'include'
            });

            if (!response.ok) {
                try {
                    const errorData = await response.json();
                    if (errorData.error?.includes('Demasiados intentos')) {
                        const seconds = parseInt(errorData.error.match(/(\d+)/)[0]);
                        const formattedTime = RateLimitService.formatTimeRemaining(seconds);
                        throw new Error(`Has excedido el límite de generación de códigos QR (10 por hora). Por favor, espera ${formattedTime} antes de intentarlo de nuevo.`);
                    }
                    throw new Error(errorData.error || 'Error al generar el código QR');
                } catch (e) {
                    if (e.message.includes('Demasiados intentos')) {
                        throw e;
                    }
                    throw new Error('No se pudo generar el código QR. Por favor, inténtalo más tarde.');
                }
            }

            const blob = await response.blob();
            return URL.createObjectURL(blob);
        } catch (error) {
            console.error('Error en generateQR:', error);
            throw error;
        }
    }

    static async validateQR(username) {
        try {
            const response = await fetch(`${AuthService.API_URL}/validate-qr/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': AuthService.getCSRFToken()
                },
                body: JSON.stringify({ username }),
                credentials: 'include'
            });

            const data = await response.json();
            
            if (!response.ok) {
                if (data.error?.includes('límite máximo de 3 usos')) {
                    return {
                        status: 'error',
                        title: messages.AUTH.RATE_LIMIT.TITLE,
                        message: messages.AUTH.RATE_LIMIT.MESSAGES.qr_uses
                    };
                }
                if (data.error?.includes('Demasiados intentos')) {
                    const seconds = parseInt(data.error.match(/(\d+)/)[0]);
                    const formattedTime = RateLimitService.formatTimeRemaining(seconds);
                    return {
                        status: 'error',
                        title: messages.AUTH.RATE_LIMIT.TITLE,
                        message: messages.AUTH.RATE_LIMIT.MESSAGES.qr_validation.replace('{time}', formattedTime)
                    };
                }
                if (data.error?.includes('expirado')) {
                    return {
                        status: 'error',
                        title: messages.AUTH.RATE_LIMIT.TITLE,
                        message: messages.AUTH.RATE_LIMIT.MESSAGES.qr_expired
                    };
                }
                if (data.error?.includes('no es válido')) {
                    return {
                        status: 'error',
                        title: 'Error de validación',
                        message: 'El código QR no es válido o ha sido manipulado'
                    };
                }
                throw new Error(data.error || 'Error al validar QR');
            }

            if (data.require_2fa) {
                return {
                    success: true,
                    require_2fa: true,
                    redirect_url: data.redirect_url
                };
            }

            return {
                success: true,
                redirect_url: data.redirect_url
            };
        } catch (error) {
            console.error('Error en validateQR:', error);
            return {
                status: 'error',
                title: 'Error',
                message: error.message || 'Error al validar QR'
            };
        }
    }

    static async get2FAStatus() {
        // Por ahora, simplemente devolver el estado almacenado en localStorage
        // hasta que implementemos el endpoint correcto
        return this.isEnabled;
    }
}
