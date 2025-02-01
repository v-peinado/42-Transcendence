import AuthService from '../AuthService.js';
import { Auth2FA } from './Auth2FA.js';

export class AuthProfile {
    static async getUserProfile() {
        try {
            const response = await fetch(`${AuthService.API_URL}/profile/user/`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'X-CSRFToken': AuthService.getCSRFToken()
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

            // Usar el estado almacenado si el servidor no proporciona uno
            const two_factor_enabled = data.two_factor_enabled !== undefined ? 
                data.two_factor_enabled : 
                Auth2FA.isEnabled;

            // Actualizar localStorage solo si el servidor proporciona un valor
            if (data.two_factor_enabled !== undefined) {
                localStorage.setItem('two_factor_enabled', data.two_factor_enabled);
            }
            
            // Convertir la URL de la imagen de perfil a una URL absoluta
            if (data.profile_image && !data.profile_image.startsWith('http')) {
                data.profile_image = `http://localhost:8000${data.profile_image}`;
            }

            if (!response.ok) {
                throw new Error(data.message || 'Error al obtener el perfil');
            }

            return {
                ...data,
                two_factor_enabled
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

            const response = await fetch(`${AuthService.API_URL}/profile/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': AuthService.getCSRFToken()
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
                return await AuthService.getUserProfile();
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

            const response = await fetch(`${AuthService.API_URL}/profile/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': AuthService.getCSRFToken(),
                },
                body: formData,
                credentials: 'include'
            });

            const data = await response.json();
            console.log('Respuesta updateProfileImage:', data);
            
            if (!response.ok) {
                throw new Error(data.message || 'Error actualizando imagen');
            }

            // Forzar una recarga del perfil completo
            return await AuthService.getUserProfile();
        } catch (error) {
            console.error('Error en updateProfileImage:', error);
            throw error;
        }
    }

    static async deleteAccount(password = null) {
        try {
            const response = await fetch(`${AuthService.API_URL}/profile/delete-account/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': AuthService.getCSRFToken()
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
}
