import AuthService from '../AuthService.js';
import RateLimitService from '../RateLimitService.js';
import { messages } from '../../translations.js';
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
                return;
            }

            const data = await response.json();

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
            const response = await fetch(`${AuthService.API_URL}/profile/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': AuthService.getCSRFToken()
                },
                body: JSON.stringify(userData),
                credentials: 'include'
            });

            let responseText = await response.text();
            try {
                // Si hay error, verificar primero si es rate limit
                if (!response.ok && responseText.includes('Please wait')) {
                    const seconds = parseInt(responseText.match(/\d+/)[0]);
                    const formattedTime = RateLimitService.formatTimeRemaining(seconds);
                    
                    return {
                        status: 'rate_limit',
                        remaining_time: seconds,
                        title: messages.AUTH.RATE_LIMIT.TITLE,
                        message: messages.AUTH.RATE_LIMIT.MESSAGES.email_verification
                            .replace('{time}', formattedTime)
                    };
                }

                // Intentar parsear como JSON
                const data = JSON.parse(responseText);
                
                if (!response.ok) {
                    throw new Error(data.error || data.message || 'Error actualizando perfil');
                }

                return data;
            } catch (e) {
                if (responseText.includes('Please wait')) {
                    const seconds = parseInt(responseText.match(/\d+/)[0]);
                    const formattedTime = RateLimitService.formatTimeRemaining(seconds);
                    
                    return {
                        status: 'rate_limit',
                        remaining_time: seconds,
                        title: messages.AUTH.RATE_LIMIT.TITLE,
                        message: messages.AUTH.RATE_LIMIT.MESSAGES.email_verification
                            .replace('{time}', formattedTime)
                    };
                }
                throw new Error(responseText);
            }
        } catch (error) {
            console.error('Error updating profile:', error);
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
