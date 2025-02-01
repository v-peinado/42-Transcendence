import { messages } from '../translations.js';

class AuthService {
    // URL base para las APIs
    static API_URL = '/api';

    static async login(username, password, remember = false) {
        try {
            // Limpiar completamente cualquier estado previo
            await this.clearSession();
            localStorage.clear();
            sessionStorage.clear();
            this.clearAllCookies();
            
            // Esperar un momento para asegurar que todo está limpio
            await new Promise(resolve => setTimeout(resolve, 100));
            
            const response = await fetch(`${this.API_URL}/login/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ 
                    username, 
                    password, 
                    remember
                }),
                credentials: 'include'
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(this.mapBackendError(data.message || 'default').html);
            }

            if (data.status === 'pending_2fa') {
                return { 
                    status: 'pending_2fa',
                    message: data.message || 'Se requiere verificación en dos pasos'
                };
            }
            
            if (data.status === 'success') {
                return {
                    status: 'success',
                    message: 'Login exitoso',
                    username: data.username
                };
            }

            throw new Error(this.mapBackendError('default').html);
        } catch (error) {
            if (!error.message.includes('alert')) {
                throw new Error(this.mapBackendError('default').html);
            }
            throw error;
        }
    }

    static mapBackendError(backendMessage) {
        // Manejar el caso cuando el mensaje viene como array desde Django
        if (Array.isArray(backendMessage)) {
            backendMessage = backendMessage[0]; // Tomar el primer mensaje
        }

        // Si el mensaje de Django es sobre credenciales inválidas
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

        // Buscar el error que coincida con el mensaje del backend o usar el default
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

    static async clearSession() {
        try {
            // Limpiar todo el estado local
            localStorage.clear();
            sessionStorage.clear();
            
            // Limpiar cookies relacionadas con la sesión
            this.clearAllCookies();
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

    static async register(userData) {
        try {
            console.log('Intentando registro con:', userData);

            const response = await fetch(`${this.API_URL}/register/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    username: userData.username.toLowerCase(),  // Añadido toLowerCase()
                    email: userData.email.toLowerCase(),       // Añadido toLowerCase()
                    password1: userData.password,             // Renombrado a password1
                    password2: userData.password2,            // Debe ser igual a password1
                    privacy_policy: true                      // Siempre true si llega aquí
                }),
                credentials: 'include'
            });
            
            // Verificar el tipo de contenido
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Respuesta del servidor no es JSON válido');
            }

            const data = await response.json();
            console.log('Respuesta del servidor:', data);
            
            if (!response.ok) {
                throw new Error(Array.isArray(data.message) ? data.message.join(', ') : data.message);
            }

            return data;
        } catch (error) {
            console.error('Error detallado en registro:', error);
            throw error;
        }
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

    static async logout() {
        try {
            const response = await fetch(`${this.API_URL}/logout/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error('Error en el logout');
            }

            // Limpiar estado local
            await this.clearSession();

            return { success: true };
        } catch (error) {
            console.error('Error en logout:', error);
            // Aún si falla la API, limpiar estado local
            await this.clearSession();
            throw error;
        }
    }

    static async verifyEmail(uid, token) {
        try {
            console.log('Intentando verificar email:', { uid, token });
            const response = await fetch(`${this.API_URL}/verify-email/${uid}/${token}/`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            });
            
            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.message || 'Error en la verificación');
            }

            const data = await response.json();
            console.log('Respuesta verificación:', data);
            return data;
        } catch (error) {
            console.error('Error verificación:', error);
            throw error;
        }
    }

    static async verifyEmailChange(uid, token) {
        try {
            console.log('Verificando cambio de email:', { uid, token });
            // Añadir slash final para coincidir con la URL de Django
            const response = await fetch(`${this.API_URL}/verify-email-change/${uid}/${token}/`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                credentials: 'include'
            });

            console.log('Respuesta del servidor:', response.status);
            const data = await response.json();
            console.log('Datos de verificación:', data);

            if (!response.ok) {
                throw new Error(data.message || 'Error en la verificación');
            }

            // Forzar actualización del estado
            await this.getUserProfile();

            return {
                success: true,
                message: data.message || 'Email actualizado correctamente'
            };
        } catch (error) {
            console.error('Error verificación cambio email:', error);
            throw error;
        }
    }

    static async getUserProfile() {
        try {
            const response = await fetch(`${this.API_URL}/profile/user/`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                credentials: 'include'
            });

            if (response.status === 401 || response.status === 403) {
                localStorage.clear();
                sessionStorage.clear();
                window.location.replace('/login');
                return { error: 'unauthorized' };
            }

            const data = await response.json();
            console.log('Respuesta getUserProfile:', data);

            // Mantener el estado 2FA en localStorage incluso si el backend no lo envía
            const two_factor_enabled = localStorage.getItem('two_factor_enabled') === 'true';
            
            // Convertir la URL de la imagen de perfil a una URL absoluta
            if (data.profile_image && !data.profile_image.startsWith('http')) {
                data.profile_image = `http://localhost:8000${data.profile_image}`;
            }

            if (!response.ok) {
                throw new Error(data.message || 'Error al obtener el perfil');
            }

            return {
                ...data,
                two_factor_enabled: data.two_factor_enabled || two_factor_enabled
            };
        } catch (error) {
            console.error('Error en getUserProfile:', error);
            return { error: error.message };
        }
    }

    static async updateProfile(userData) {
        try {
            const data = {};
            if (userData.email) data.email = userData.email;
            if (userData.current_password) {
                data.current_password = userData.current_password;
                data.new_password1 = userData.new_password1;
                data.new_password2 = userData.new_password2;
            }
            // Añadir el flag de restauración si existe
            if (userData.restore_image) {
                data.restore_image = true;
            }

            const response = await fetch(`${this.API_URL}/profile/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(data),
                credentials: 'include'
            });

            const responseData = await response.json();
            console.log('Respuesta actualización:', responseData);

            if (!response.ok) {
                throw new Error(responseData.message || responseData.error || 'Error actualizando perfil');
            }

            // Si estamos restaurando la imagen, forzar una recarga del perfil
            if (userData.restore_image) {
                return await this.getUserProfile();
            }

            return {
                success: true,
                message: responseData.message,
                requiresVerification: userData.email ? true : false
            };
        } catch (error) {
            console.error('Error en updateProfile:', error);
            throw error;
        }
    }

    static async updateProfileImage(imageFile) {
        try {
            const formData = new FormData();
            formData.append('profile_image', imageFile);

            const response = await fetch(`${this.API_URL}/profile/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                },
                body: formData,
                credentials: 'include'
            });

            const data = await response.json();
            console.log('Respuesta updateProfileImage:', data); // Añadir este log
            
            if (!response.ok) {
                throw new Error(data.message || 'Error actualizando imagen');
            }

            // Forzar una recarga del perfil completo
            return await this.getUserProfile();
        } catch (error) {
            console.error('Error en updateProfileImage:', error);
            throw error;
        }
    }

    static async requestPasswordReset(email) {
        try {
            const response = await fetch(`${this.API_URL}/password/reset/`, {  // Cambiada la URL
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ email }),
                credentials: 'include'
            });
            
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.message || 'Error al solicitar el reset');
            }
            return data;
        } catch (error) {
            throw error;
        }
    }

    static async resetPassword(uidb64, token, password1, password2) {
        try {
            const response = await fetch(`${this.API_URL}/password/reset/confirm/`, {  // Cambiada la URL
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    uidb64,
                    token,
                    new_password1: password1,
                    new_password2: password2
                }),
                credentials: 'include'
            });
            
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.message || 'Error al resetear la contraseña');
            }
            return data;
        } catch (error) {
            throw error;
        }
    }

    static async deleteAccount(password = null) {
        try {
            const response = await fetch(`${this.API_URL}/profile/delete-account/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(password ? { confirm_password: password } : {}),
                credentials: 'include'
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.message);
            }

            return true;
        } catch (error) {
            throw error;
        }
    }

    static async getGDPRSettings() {
        try {
            // Obtener política de privacidad
            const policyResponse = await fetch(`${this.API_URL}/gdpr/privacy-policy/`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                credentials: 'include'
            });

            // Obtener datos personales
            const dataResponse = await fetch(`${this.API_URL}/gdpr/export-data/`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
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
            const response = await fetch(`${this.API_URL}/gdpr/data/`, { // Cambiado a /gdpr/data/
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
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
            const response = await fetch(`${this.API_URL}/gdpr/export-data/`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
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

    static async get42AuthUrl() {
        try {
            const response = await fetch(`${this.API_URL}/authentication/42/api/login/`, {
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
            console.log('AuthService: Enviando código a backend:', code);
            
            const response = await fetch(`${this.API_URL}/authentication/42/api/callback/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ code }), // Este es el código de autorización de 42
                credentials: 'include'
            });

            const data = await response.json();
            console.log('AuthService: Respuesta del servidor:', data);

            // Si el usuario necesita verificar email primero
            if (data.needsEmailVerification) {
                return {
                    status: 'pending_verification',
                    message: messages.AUTH.EMAIL_VERIFICATION.MESSAGE
                };
            }

            // Si el usuario está verificado y tiene 2FA
            if (data.require_2fa) {
                return {
                    status: 'pending_2fa',
                    username: data.username,
                    message: 'Se requiere verificación en dos pasos'
                };
            }

            // Si todo está ok y no necesita 2FA
            if (data.status === 'success') {
                localStorage.setItem('isAuthenticated', 'true');
                localStorage.setItem('username', data.username);
                window.location.replace('/profile');  // Cambiar '/user' por '/profile'
            }

            throw new Error(data.message || messages.AUTH.ERRORS.LOGIN_FAILED);
        } catch (error) {
            console.error('AuthService: Error detallado:', error);
            throw error;
        }
    }

    // Esta es la que está causando el problema
    static async handleFortyTwoCallback(code) {
        try {
            const response = await fetch('/api/auth/42/callback', {  // ❌ URL incorrecta
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ code })
            });

            const data = await response.json();

            if (data.require_2fa) {
                // Guardar estado temporal para 2FA
                sessionStorage.setItem('pendingAuth', 'true');
                sessionStorage.setItem('fortytwo_user', 'true');
                return { requireTwoFactor: true };
            }

            if (data.status === 'success') {
                localStorage.setItem('isAuthenticated', 'true');
                localStorage.setItem('username', data.username);
                return { success: true };
            }

            throw new Error(data.message);
        } catch (error) {
            throw new Error(error.message || 'Error en la autenticación con 42');
        }
    }

    static async enable2FA() {
        try {
            const response = await fetch(`${this.API_URL}/enable-2fa/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                credentials: 'include'
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || 'Error al activar 2FA');
            }

            // Actualizar estado local
            localStorage.setItem('two_factor_enabled', 'true');

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
            const response = await fetch(`${this.API_URL}/disable-2fa/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                credentials: 'include'
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || 'Error al desactivar 2FA');
            }

            // Limpiar estado local
            localStorage.removeItem('two_factor_enabled');

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
            
            // Corregir la ruta para que coincida con la URL en Django
            const endpoint = isFortytwoUser ? 
                `${this.API_URL}/auth/42/verify-2fa/` :  // Usar la misma ruta que en Django
                `${this.API_URL}/verify-2fa/`;
            
            console.log('Usando endpoint:', endpoint);  // Debug

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ code }), // Este es el código 2FA
                credentials: 'include'
            });

            // Debug para ver la respuesta raw
            const responseText = await response.text();
            console.log('Respuesta raw:', responseText);

            let data;
            try {
                data = JSON.parse(responseText);
            } catch (e) {
                console.error('Error parseando respuesta:', e);
                throw new Error('Error en la respuesta del servidor');
            }

            if (!response.ok) {
                throw new Error(data.error || data.message || 'Código inválido');
            }

            if (data.status === 'success') {
                window.location.replace('/profile');  // Cambiar de '/user' a '/profile'
            }

            return {
                status: 'success',
                username: data.username || sessionStorage.getItem('pendingUsername'),
                two_factor_enabled: true
            };
        } catch (error) {
            console.error('Error en verify2FA:', error);
            throw error;
        }
    }

    static async generateQR(username) {
        try {
            const response = await fetch(`${this.API_URL}/generate-qr/${username}/`, {
                method: 'GET',
                headers: {
                    'Accept': 'image/png',
                    'X-CSRFToken': this.getCSRFToken()
                },
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error('Error generando código QR');
            }

            // Convertir la respuesta a blob
            const blob = await response.blob();
            return URL.createObjectURL(blob);
        } catch (error) {
            console.error('Error en generateQR:', error);
            throw error;
        }
    }

    async validateQR(username) {
        try {
            const response = await fetch('/api/validate-qr/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                credentials: 'include',
                body: JSON.stringify({ username })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Error validando el código QR');
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error en validateQR:', error);
            throw error;
        }
    }

    static async validateQR(username) {
        try {
            const response = await fetch(`${this.API_URL}/validate-qr/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ username }),
                credentials: 'include'
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || 'Error al validar QR');
            }

            // Verificar si requiere 2FA
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
}

export default AuthService;
