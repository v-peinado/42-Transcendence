import AuthService from '../../services/AuthService.js';

export function ResetPasswordView(uidb64, token) {
    const app = document.getElementById('app');
    app.innerHTML = `
        <div class="hero-section">
            <div class="container">
                <div class="row justify-content-center">
                    <div class="col-md-6 col-lg-5">
                        <div class="card login-card">
                            <div class="card-body p-5">
                                <h3 class="text-light mb-4 text-center">Establecer nueva contraseña</h3>
                                <form id="resetPasswordForm">
                                    <div class="mb-3">
                                        <label class="form-label">Nueva Contraseña</label>
                                        <input type="password" class="form-control" id="password1" required>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">Confirmar Contraseña</label>
                                        <input type="password" class="form-control" id="password2" required>
                                    </div>
                                    <div id="messageArea" class="alert d-none mb-3"></div>
                                    <div class="d-grid">
                                        <button type="submit" class="btn btn-primary">
                                            Establecer Contraseña
                                        </button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    document.getElementById('resetPasswordForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const password1 = document.getElementById('password1').value;
        const password2 = document.getElementById('password2').value;
        const messageArea = document.getElementById('messageArea');

        try {
            const result = await AuthService.resetPassword(uidb64, token, password1, password2);
            messageArea.classList.remove('d-none', 'alert-danger');
            messageArea.classList.add('alert-success');
            messageArea.textContent = 'Contraseña actualizada correctamente';

            // Redirigir al login después de 2 segundos
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);
        } catch (error) {
            messageArea.classList.remove('d-none', 'alert-success');
            messageArea.classList.add('alert-danger');
            messageArea.textContent = error.message || 'Error al actualizar la contraseña';
        }
    });
}
