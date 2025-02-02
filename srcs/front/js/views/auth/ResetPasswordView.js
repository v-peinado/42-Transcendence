import AuthService from '../../services/AuthService.js';
import { loadHTML } from '../../utils/htmlLoader.js';

export async function ResetPasswordView(uidb64, token) {
    const app = document.getElementById('app');
    app.textContent = ''; // Limpiar de forma segura

    // Cargar y mostrar el template
    const parser = new DOMParser();
    const html = await loadHTML('/views/auth/password/ResetPassword.html');
    const content = parser.parseFromString(html, 'text/html').body.firstElementChild;
    app.appendChild(content);

    // Manejar el envío del formulario
    const form = document.getElementById('resetPasswordForm');
    const messageArea = document.getElementById('messageArea');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const password1 = document.getElementById('password1').value;
        const password2 = document.getElementById('password2').value;

        try {
            const result = await AuthService.resetPassword(uidb64, token, password1, password2);
            messageArea.textContent = 'Contraseña actualizada correctamente';
            messageArea.className = 'alert alert-success mb-3';

            // Redirigir al login después de 2 segundos
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);
        } catch (error) {
            messageArea.textContent = error.message || 'Error al actualizar la contraseña';
            messageArea.className = 'alert alert-danger mb-3';
        }
    });
}
