import AuthService from '../../services/AuthService.js';

export function RequestPasswordResetView() {
    const app = document.getElementById('app');
    app.innerHTML = `
        <div class="hero-section">
            <div class="container">
                <div class="row justify-content-center">
                    <div class="col-md-6 col-lg-5">
                        <div class="card login-card">
                            <div class="card-body p-5">
                                <h3 class="text-light mb-4 text-center">Recuperar Contraseña</h3>
                                <form id="passwordResetForm">
                                    <div class="mb-3">
                                        <label class="form-label">Email</label>
                                        <input type="email" class="form-control" id="email" required>
                                    </div>
                                    <div id="messageArea" class="alert d-none mb-3"></div>
                                    <div class="d-grid">
                                        <button type="submit" class="btn btn-primary">
                                            <i class="fas fa-paper-plane me-2"></i>Enviar
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

    document.getElementById('passwordResetForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('email').value;
        try {
            const result = await AuthService.requestPasswordReset(email);
            document.getElementById('messageArea').innerHTML = `
                <div class="alert alert-success">${result.message}</div>
            `;
            document.getElementById('messageArea').classList.remove('d-none');
        } catch (error) {
            document.getElementById('messageArea').innerHTML = `
                <div class="alert alert-danger">${error.message}</div>
            `;
            document.getElementById('messageArea').classList.remove('d-none');
        }
    });
}