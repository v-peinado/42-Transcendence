import AuthService from '../AuthService.js';

export class AuthPassword {
    static async requestPasswordReset(email) {
        try {
            const response = await fetch(`${AuthService.API_URL}/password/reset/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': AuthService.getCSRFToken()
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
            const response = await fetch(`${AuthService.API_URL}/password/reset/confirm/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': AuthService.getCSRFToken()
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
}
