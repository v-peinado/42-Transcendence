import AuthService from '../../services/AuthService.js';
import { loadHTML } from '../../utils/htmlLoader.js';

export async function RequestPasswordResetView() {
    const app = document.getElementById('app');
    app.textContent = ''; // Limpiar de forma segura

    // Cargar y mostrar el template
    const parser = new DOMParser();
    const html = await loadHTML('/views/auth/password/RequestPasswordReset.html');
    const content = parser.parseFromString(html, 'text/html').body.firstElementChild;
    app.appendChild(content);

    // Manejar el envío del formulario
    const form = document.getElementById('passwordResetForm');
    const messageArea = document.getElementById('messageArea');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('email').value;
        
        try {
            const result = await AuthService.requestPasswordReset(email);
            messageArea.textContent = result.message;
            messageArea.className = 'alert alert-success mb-3';
        } catch (error) {
            messageArea.textContent = error.message;
            messageArea.className = 'alert alert-danger mb-3';
        }
    });
}