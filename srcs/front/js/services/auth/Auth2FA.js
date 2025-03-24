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
            if (!navigator.onLine) {
                return {
                    status: 'error',
                    title: 'Error de conexión',
                    message: 'No hay conexión a internet'
                };
            }

            const endpoint = isFortytwoUser ? 
                `${AuthService.API_URL}/auth/42/verify-2fa/` :
                `${AuthService.API_URL}/verify-2fa/`;
            
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000);

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': AuthService.getCSRFToken()
                },
                body: JSON.stringify({ code }),
                credentials: 'include',
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            let data = await response.json();

            if (!response.ok) {
                // Si es error 400, es código inválido
                if (response.status === 400) {
                    // Llevar la cuenta de intentos en sessionStorage
                    const attempts = parseInt(sessionStorage.getItem('2fa_attempts') || '0') + 1;
                    sessionStorage.setItem('2fa_attempts', attempts.toString());

                    if (attempts >= 3) {
                        // Si alcanza el límite, mostrar mensaje de bloqueo
                        return {
                            status: 'rate_limit',
                            remaining_time: 900, // 15 minutos
                            title: messages.AUTH.RATE_LIMIT.TITLE,
                            message: messages.AUTH.RATE_LIMIT.MESSAGES.two_factor
                                .replace('{time}', RateLimitService.formatTimeRemaining(900))
                        };
                    }

                    // Si aún no alcanza el límite, mostrar intentos restantes
                    return {
                        status: 'error',
                        title: 'Código incorrecto',
                        message: `Código incorrecto. Te quedan ${3 - attempts} intentos.`
                    };
                }

                // Si es rate limit
                if (data.error?.includes('Demasiados intentos')) {
                    const seconds = parseInt(data.error.match(/(\d+)/)[0]);
                    return Auth2FA._formatRateLimitResponse(seconds);
                }

                throw new Error(data.error || data.message || 'Error en la verificación');
            }

            if (data.status === 'success') {
                localStorage.setItem('isAuthenticated', 'true');
                if (data.username) {
                    localStorage.setItem('username', data.username);
                }
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
            
            if (error.name === 'AbortError') {
                return {
                    status: 'error',
                    title: 'Tiempo de espera agotado',
                    message: 'El servidor está tardando demasiado en responder'
                };
            }

            return {
                status: 'error',
                title: 'Error de verificación',
                message: messages.AUTH.ERRORS.INVALID_2FA_CODE
            };
        }
    }

    static _formatRateLimitResponse(seconds) {
        if (!seconds || isNaN(seconds)) {
            return {
                status: 'error',
                title: 'Error de verificación',
                message: 'Error al procesar el límite de intentos'
            };
        }

        const formattedTime = RateLimitService.formatTimeRemaining(seconds);
        return {
            status: 'rate_limit',
            remaining_time: seconds,
            title: messages.AUTH.RATE_LIMIT.TITLE,
            message: messages.AUTH.RATE_LIMIT.MESSAGES.two_factor
                .replace('{time}', formattedTime)
                .replace('{attempts}', '3')  // Añadir número de intentos al mensaje
        };
    }

    static _handleVerificationError(error) {
        if (!error) {
            return {
                status: 'error',
                title: 'Error desconocido',
                message: 'Ha ocurrido un error al verificar el código'
            };
        }

        console.error('2FA error details:', error);

        // Verificar rate limit en el mensaje de error
        const rateLimitMatch = error.message?.match(/(?:Demasiados intentos|Too many attempts).*?(\d+)/i);
        if (rateLimitMatch) {
            return Auth2FA._formatRateLimitResponse(parseInt(rateLimitMatch[1]));
        }

        // Para cualquier otro error, mostrar mensaje específico si existe
        return {
            status: 'error',
            title: 'Error de verificación',
            message: error.message && error.message !== 'Error en la verificación' 
                ? error.message 
                : 'El código introducido no es correcto'
        };
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
