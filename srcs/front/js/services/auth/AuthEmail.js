import AuthService from '../AuthService.js';
import RateLimitService from '../RateLimitService.js';
import { messages } from '../../translations.js';

export class AuthEmail {
    static async verifyEmail(uid, token) {
        try {
            console.log('Intentando verificar email:', { uid, token });
            const response = await fetch(`${AuthService.API_URL}/verify-email/${uid}/${token}/`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            });
            
            let responseText;
            try {
                responseText = await response.text();
                const data = JSON.parse(responseText);
                
                if (!response.ok) {
                    // Verificar rate limit
                    if (responseText.includes('Please wait') && responseText.includes('seconds')) {
                        const seconds = parseInt(responseText.match(/\d+/)[0]);
                        const formattedTime = RateLimitService.formatTimeRemaining(seconds);
                        
                        return {
                            status: 'rate_limit',
                            remaining_time: seconds,
                            title: messages.AUTH.RATE_LIMIT.TITLE,
                            message: messages.AUTH.RATE_LIMIT.MESSAGES.email_verification.replace('{time}', formattedTime)
                        };
                    }
                    throw new Error(data.message || 'Error en la verificación');
                }
                return data;
            } catch (e) {
                // Si es error de rate limit
                if (responseText.includes('Please wait') && responseText.includes('seconds')) {
                    const seconds = parseInt(responseText.match(/\d+/)[0]);
                    const formattedTime = RateLimitService.formatTimeRemaining(seconds);
                    
                    return {
                        status: 'rate_limit',
                        remaining_time: seconds,
                        title: messages.AUTH.RATE_LIMIT.TITLE,
                        message: messages.AUTH.RATE_LIMIT.MESSAGES.email_verification.replace('{time}', formattedTime)
                    };
                }
                throw new Error(responseText);
            }
        } catch (error) {
            if (RateLimitService.isRateLimited(error)) {
                return RateLimitService.handleRateLimit(error, 'email_verification');
            }
            console.error('Error verificación:', error);
            throw error;
        }
    }

    static async verifyEmailChange(uid, token) {
        try {
            console.log('Verificando cambio de email:', { uid, token });
            const response = await fetch(`${AuthService.API_URL}/verify-email-change/${uid}/${token}/`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'X-CSRFToken': AuthService.getCSRFToken()
                },
                credentials: 'include'
            });

            let responseText;
            try {
                responseText = await response.text();
                const data = JSON.parse(responseText);

                if (!response.ok) {
                    // Verificar si es rate limit
                    if (responseText.includes('Please wait') && responseText.includes('seconds')) {
                        const seconds = parseInt(responseText.match(/\d+/)[0]);
                        const formattedTime = RateLimitService.formatTimeRemaining(seconds);
                        
                        return {
                            status: 'rate_limit',
                            remaining_time: seconds,
                            title: messages.AUTH.RATE_LIMIT.TITLE,
                            message: messages.AUTH.RATE_LIMIT.MESSAGES.email_verification.replace('{time}', formattedTime)
                        };
                    }
                    throw new Error(data.message || 'Error en la verificación');
                }
                console.log('Respuesta del servidor:', response.status);
                console.log('Datos de verificación:', data);

                await AuthService.getUserProfile();

                return {
                    success: true,
                    message: data.message || 'Email actualizado correctamente'
                };
            } catch (e) {
                // Si el texto contiene mensaje de rate limit
                if (responseText && responseText.includes('Please wait')) {
                    const seconds = parseInt(responseText.match(/\d+/)[0]);
                    const formattedTime = RateLimitService.formatTimeRemaining(seconds);
                    
                    return {
                        status: 'rate_limit',
                        remaining_time: seconds,
                        title: messages.AUTH.RATE_LIMIT.TITLE,
                        message: messages.AUTH.RATE_LIMIT.MESSAGES.email_verification.replace('{time}', formattedTime)
                    };
                }
                throw new Error(responseText);
            }
        } catch (error) {
            console.error('Error verificación cambio email:', error);
            throw error;
        }
    }
}
