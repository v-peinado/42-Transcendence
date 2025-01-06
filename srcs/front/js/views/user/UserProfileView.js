import AuthService from '../../services/AuthService.js';

export function UserProfileView() {
    const app = document.getElementById('app');
    app.innerHTML = `
        <div class="container mt-4">
            <div class="row">
                <!-- Sidebar -->
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body">
                            <div class="d-flex flex-column align-items-center text-center">
                                <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='150' height='150' viewBox='0 0 150 150'%3E%3Ccircle cx='75' cy='75' r='75' fill='%23e9ecef'/%3E%3Cpath d='M75 75c-20.711 0-37.5-16.789-37.5-37.5S54.289 0 75 0s37.5 16.789 37.5 37.5S95.711 75 75 75zm25 12.5H50C22.386 87.5 0 109.886 0 137.5V150h150v-12.5c0-27.614-22.386-50-50-50z' fill='%23adb5bd'/%3E%3C/svg%3E" class="rounded-circle" width="150" alt="Avatar">
                                <div class="mt-3" id="userInfo">
                                    <h4>Cargando...</h4>
                                </div>
                            </div>
                            <hr>
                            <div class="d-grid gap-2">
                                <button id="logoutBtn" class="btn btn-danger">Cerrar Sesión</button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Main Content -->
                <div class="col-md-9">
                    <div class="card">
                        <div class="card-body">
                            <h4>Mi Perfil</h4>
                            <hr>
                            <div id="profileData">Cargando datos del perfil...</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Cargar datos del usuario
    loadUserData();

    // Event Listeners
    document.getElementById('logoutBtn').addEventListener('click', async () => {
        try {
            await AuthService.logout();
            window.location.href = '/login';
        } catch (error) {
            console.error('Error en logout:', error);
        }
    });
}

async function loadUserData() {
    try {
        const userInfo = await AuthService.getUserProfile();
        document.getElementById('userInfo').innerHTML = `
            <h4>${userInfo.username}</h4>
            <p class="text-secondary mb-1">${userInfo.email}</p>
        `;
        
        document.getElementById('profileData').innerHTML = `
            <dl class="row">
                <dt class="col-sm-3">Username:</dt>
                <dd class="col-sm-9">${userInfo.username}</dd>
                
                <dt class="col-sm-3">Email:</dt>
                <dd class="col-sm-9">${userInfo.email}</dd>
                
                <dt class="col-sm-3">Estado:</dt>
                <dd class="col-sm-9">
                    <span class="badge bg-${userInfo.is_active ? 'success' : 'warning'}">
                        ${userInfo.is_active ? 'Activo' : 'Pendiente'}
                    </span>
                </dd>
            </dl>
        `;
    } catch (error) {
        console.error('Error cargando datos:', error);
    }
}
