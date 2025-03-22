import { messages } from '../translations.js';

class RateLimitService {
    static formatTimeRemaining(seconds) {
        if (seconds < 60) {
            return `${seconds} segundos`;
        }
        
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        
        if (minutes < 60) {
            if (remainingSeconds === 0) {
                return minutes === 1 ? '1 minuto' : `${minutes} minutos`;
            }
            return `${minutes} ${minutes === 1 ? 'minuto' : 'minutos'} y ${remainingSeconds} segundos`;
        }
        
        const hours = Math.floor(minutes / 60);
        const remainingMinutes = minutes % 60;
        
        if (hours < 24) {
            if (remainingMinutes === 0) {
                return hours === 1 ? '1 hora' : `${hours} horas`;
            }
            return `${hours} ${hours === 1 ? 'hora' : 'horas'} y ${remainingMinutes} minutos`;
        }
        
        const days = Math.floor(hours / 24);
        const remainingHours = hours % 24;
        
        if (remainingHours === 0) {
            return days === 1 ? '1 día' : `${days} días`;
        }
        return `${days} ${days === 1 ? 'día' : 'días'} y ${remainingHours} horas`;
    }

    static handleRateLimit(response, action = 'login') {
        if (response.status === 429) {
            const seconds = response.data.remaining_time || 900;
            const formattedTime = this.formatTimeRemaining(seconds);
            
            return {
                status: 'rate_limit',
                remaining_time: seconds,
                title: messages.AUTH.RATE_LIMIT.TITLE,
                message: messages.AUTH.RATE_LIMIT.MESSAGES[action].replace('{time}', formattedTime)
            };
        }
        return null;
    }

    static isRateLimited(error) {
        return error.status === 429 || 
               (error.response?.status === 429) || 
               (error.message && error.message.includes('Too many attempts'));
    }
}

export default RateLimitService;
