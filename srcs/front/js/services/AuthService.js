// js/views/auth/LoginView.js
// (empty file)

// js/views/auth/RegisterView.js
// (empty file)

// js/services/AuthService.js
class AuthService {
    // URL base para las APIs
    static API_URL = '/api';

    static async login(username, password, remember = false) {
        try {
            console.log('Intentando login con:', { username, remember });
            const response = await fetch(`${this.API_URL}/login/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ 
                    username: username, 
                    password: password, 
                    remember: remember 
                }),
                credentials: 'include'  // Importante para las cookies
            });
            
            const data = await response.json();
            console.log('Respuesta del servidor:', data);
            
            if (!response.ok) {
                // Manejar específicamente el caso de email no verificado
                if (data.message && data.message.includes('verifica tu email')) {
                    return {
                        success: false,
                        needsEmailVerification: true,
                        message: data.message
                    };
                }
                const errorMessage = Array.isArray(data.message) 
                    ? data.message.join(', ') 
                    : data.message || 'Error en el login';
                console.error('Error de login:', errorMessage);
                throw new Error(errorMessage);
            }

            return {
                success: data.status === 'success',
                redirectUrl: data.redirect_url || '/',
                pending2FA: data.status === 'pending_2fa',
                message: data.message
            };
        } catch (error) {
            console.error('Error en login:', error);
            throw error;
        }
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
                    'Accept': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.message || 'Logout failed');
            }
            
            return { success: true, message: data.message };
        } catch (error) {
            console.error('Error en logout:', error);
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

    static async getUserProfile() {
        try {
            const response = await fetch(`${this.API_URL}/profile/user/`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                credentials: 'include'  // Importante para las cookies de sesión
            });

            if (!response.ok) {
                throw new Error('Error al obtener el perfil');
            }

            const data = await response.json();
            console.log('Datos del perfil recibidos:', data);  // Debug
            return data;
        } catch (error) {
            console.error('Error en getUserProfile:', error);
            throw new Error('No se pudo cargar el perfil de usuario');
        }
    }
}

export default AuthService;
