import { messages } from '../translations.js';

class RateLimitService {
    static formatTimeRemaining(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        
        if (minutes === 0) {
            return `${remainingSeconds} segundos`;
        }
        
        if (minutes === 1) {
            if (remainingSeconds === 0) {
                return '1 minuto';
            }
            return `1 minuto y ${remainingSeconds} segundos`;
        }
        
        if (remainingSeconds === 0) {
            return `${minutes} minutos`;
        }
        return `${minutes} minutos y ${remainingSeconds} segundos`;
    }

    static getMessage(action, seconds) {
        const formattedTime = this.formatTimeRemaining(seconds);
        return {
            status: 'rate_limit',
            remaining_time: seconds,
            title: messages.AUTH.RATE_LIMIT.TITLE,
            message: messages.AUTH.RATE_LIMIT.MESSAGES[action].replace('{time}', formattedTime)
        };
    }
}

export default RateLimitService;
