import AuthService from '../../services/AuthService.js';

export function UserView() {
    const app = document.getElementById('app');
    app.innerHTML = `
        <div class="container mt-4">
            <div class="card">
                <div class="card-body">
                    <h3 class="card-title">Panel de Usuario</h3>
                    <div class="d-grid gap-2">
                        <a href="/profile/edit" data-link class="btn btn-primary mb-2">Editar Perfil</a>
                        <a href="/game" data-link class="btn btn-success mb-2">Jugar</a>
                        <button id="logoutBtn" class="btn btn-danger">Cerrar Sesión</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    document.getElementById('logoutBtn').addEventListener('click', async () => {
        try {
            await AuthService.logout();
            window.location.href = '/login';
        } catch (error) {
            console.error('Error en logout:', error);
        }
    });
}
