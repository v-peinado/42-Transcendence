import AuthService from '../AuthService.js';

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
            
            console.log('Usando endpoint:', endpoint);

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

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || data.message || 'Código inválido');
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
            console.error('Error en verify2FA:', error);
            throw error;
        }
    }

    static async generateQR(username) {
        try {
            const response = await fetch(`${AuthService.API_URL}/generate-qr/${username}/`, {
                method: 'GET',
                headers: {
                    'Accept': 'image/png',
                    'X-CSRFToken': AuthService.getCSRFToken()
                },
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error('Error generando código QR');
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
                throw new Error(data.message || 'Error al validar QR');
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
            throw error;
        }
    }

    static async get2FAStatus() {
        try {
            const response = await fetch(`${AuthService.API_URL}/2fa-status/`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'X-CSRFToken': AuthService.getCSRFToken()
                },
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error('Error al obtener estado 2FA');
            }

            const data = await response.json();
            this.isEnabled = data.enabled; // Esto actualiza localStorage y la UI
            return data.enabled;
        } catch (error) {
            console.error('Error al obtener estado 2FA:', error);
            return this.isEnabled;
        }
    }
}
