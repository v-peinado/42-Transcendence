export class AlertService {
    static show(message, type = 'info', duration = 3000) {
        const alertEl = document.createElement('div');
        alertEl.className = `alert alert-${type} fade show position-fixed`;
        alertEl.style.top = '20px';
        alertEl.style.right = '20px';
        alertEl.style.zIndex = '1050';
        alertEl.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} me-2"></i>
            ${message}
        `;
        
        document.body.appendChild(alertEl);
        setTimeout(() => {
            alertEl.remove();
        }, duration);
    }
}
