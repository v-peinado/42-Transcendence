import AuthService from '../AuthService.js';
import { AuthUtils } from './AuthUtils.js';

export class AuthRegister {
    static async register(userData) {
        try {
            console.log('Intentando registro con:', userData);

            const response = await fetch(`${AuthService.API_URL}/register/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': AuthUtils.getCSRFToken()
                },
                body: JSON.stringify({
                    username: userData.username.toLowerCase(),
                    email: userData.email.toLowerCase(),
                    password1: userData.password,
                    password2: userData.password2,
                    privacy_policy: true
                }),
                credentials: 'include'
            });
            
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
}
