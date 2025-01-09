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
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (!response.ok) {
                throw new Error('Error en logout');
            }

            // Limpiar todo el estado del usuario
            localStorage.clear();
            sessionStorage.clear();
            
            // Limpiar todas las cookies relacionadas con la sesión
            document.cookie.split(";").forEach(cookie => {
                document.cookie = cookie
                    .replace(/^ +/, "")
                    .replace(/=.*/, `=;expires=${new Date().toUTCString()};path=/`);
            });

            return true;
        } catch (error) {
            console.error('Error durante logout:', error);
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

    static async updateProfile(userData) {
        try {
            const data = {};
            if (userData.email) data.email = userData.email;
            if (userData.current_password) {
                data.current_password = userData.current_password;
                data.new_password1 = userData.new_password1;
                data.new_password2 = userData.new_password2;
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

    static async deleteAccount(password) {
        try {
            const response = await fetch(`${this.API_URL}/profile/delete-account/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ confirm_password: password }),
                credentials: 'include'
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.message || 'Error al eliminar la cuenta');
            }

            // Limpiar estado de usuario inmediatamente
            localStorage.clear();
            sessionStorage.clear();
            
            return { success: true };
        } catch (error) {
            console.error('Error en deleteAccount:', error);
            throw error;
        }
    }
}

export default AuthService;
