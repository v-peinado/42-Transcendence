class AuthService {
    // URL base para las APIs
    static API_URL = '/api';

    static async login(username, password, remember = false) {
        try {
            // Asegurarse de que no hay sesión activa
            await this.clearSession();
            
            // Esperar un momento para asegurar que todo está limpio
            await new Promise(resolve => setTimeout(resolve, 100));
            
            console.log('Enviando request de login...'); // Debug
            
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
            console.log('Respuesta login:', data);
            
            if (!response.ok) {
                throw new Error(data.message || 'Error en el login');
            }

            // Si requiere 2FA, NO establecer autenticación todavía
            if (data.status === 'pending_2fa') {
                console.log('Backend requiere 2FA');
                return { 
                    status: 'pending_2fa',
                    message: data.message || 'Se requiere verificación en dos pasos'
                };
            }

            // Solo establecer autenticación si el login es exitoso y no requiere 2FA
            if (data.status === 'success') {
                return {
                    status: 'success',
                    message: 'Login exitoso'
                };
            }

            throw new Error(data.message || 'Error desconocido en el login');
        } catch (error) {
            console.error('Error en login service:', error);
            throw error;
        }
    }

    static async clearSession() {
        try {
            // Limpiar todo el estado local primero
            localStorage.clear();
            sessionStorage.clear();
            
            // Limpiar todas las cookies relacionadas
            this.clearAllCookies();
            
            // Solo entonces intentar el logout en el backend
            try {
                await fetch(`${this.API_URL}/logout/`, {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken()
                    }
                });
            } catch (error) {
                console.warn('Error en logout backend:', error);
                // Continuar incluso si falla el logout del backend
            }
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
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            // Esperar la respuesta antes de limpiar
            await response.json();
        } catch (error) {
            console.error('Error durante logout:', error);
        } finally {
            await this.clearSession();
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
            const sessionId = localStorage.getItem('sessionId');
            const headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            };

            if (sessionId) {
                headers['X-Session-ID'] = sessionId;
            }

            const response = await fetch(`${this.API_URL}/profile/user/`, {
                method: 'GET',
                headers: headers,
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

            if (!response.ok) {
                throw new Error(data.message || 'Error al obtener el perfil');
            }

            return data;
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

    static async updateProfileImage(imageFile) {
        try {
            const formData = new FormData();
            formData.append('profile_image', imageFile);

            const response = await fetch(`${this.API_URL}/profile/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    // No incluir Content-Type, fetch lo establecerá automáticamente con el boundary
                },
                body: formData,
                credentials: 'include'
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || 'Error actualizando imagen');
            }

            return data;
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
                body: JSON.stringify({ code }),
                credentials: 'include'
            });

            const data = await response.json();
            console.log('AuthService: Respuesta del servidor:', data);
            
            if (response.ok && data.status === 'success') {
                // Usuario autenticado correctamente
                return {
                    status: 'success',
                    username: data.username
                };
            } else if (response.ok && data.is_verified) {
                // Usuario ya verificado
                return {
                    status: 'verified',
                    username: data.username
                };
            } else {
                // Necesita verificación o hay error
                return {
                    status: 'error',
                    needsEmailVerification: true,
                    message: data.message || 'Error en la autenticación'
                };
            }
        } catch (error) {
            console.error('AuthService: Error detallado:', error);
            throw error;
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

            return data;
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

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || 'Error al desactivar 2FA');
            }

            return await response.json();
        } catch (error) {
            throw error;
        }
    }

    static async verify2FACode(code) {
        try {
            console.log('Verificando código 2FA:', code);
            
            const response = await fetch(`${this.API_URL}/verify-2fa/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ code }),
                credentials: 'include'
            });

            const data = await response.json();
            console.log('Respuesta verify2FA:', data);

            if (!response.ok) {
                throw new Error(data.error || data.message || 'Código inválido');
            }

            if (data.status === 'success') {
                // Asegurarnos de que la sesión está establecida
                const username = data.username || sessionStorage.getItem('pendingUsername');
                
                // Establecer autenticación
                localStorage.setItem('isAuthenticated', 'true');
                localStorage.setItem('username', username);
                localStorage.setItem('sessionId', data.session_id);
                
                // Limpiar estado temporal
                sessionStorage.removeItem('pendingAuth');
                sessionStorage.removeItem('pendingUsername');
                
                // Forzar actualización de CSRF token
                document.cookie = `csrftoken=${this.getCSRFToken()}; path=/`;
                
                return {
                    status: 'success',
                    username: username
                };
            }

            throw new Error('Error en la verificación');
        } catch (error) {
            console.error('Error en verify2FA:', error);
            throw error;
        }
    }
}

export default AuthService;
