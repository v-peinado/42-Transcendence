import AuthService from '../../services/AuthService.js';

export function VerifyEmailChangeView(uid, token) {
    const app = document.getElementById('app');
    
    // Pantalla de carga inicial
    app.innerHTML = `
        <div class="hero-section">
            <div class="container">
                <div class="row justify-content-center">
                    <div class="col-md-6 text-center">
                        <h3 class="text-light mb-4">Verificando cambio de email...</h3>
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Cargando...</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Verificar el cambio de email
    AuthService.verifyEmailChange(uid, token)
        .then(result => {
            app.innerHTML = `
                <div class="hero-section">
                    <div class="container">
                        <div class="row justify-content-center">
                            <div class="col-md-6 text-center">
                                <h3 class="text-light mb-4">¡Email Actualizado!</h3>
                                <div class="alert alert-success">
                                    ${result.message}
                                </div>
                                <a href="/profile" data-link class="btn btn-primary">
                                    Ir a mi perfil
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        })
        .catch(error => {
            app.innerHTML = `
                <div class="hero-section">
                    <div class="container">
                        <div class="row justify-content-center">
                            <div class="col-md-6 text-center">
                                <h3 class="text-light mb-4">Error al verificar email</h3>
                                <div class="alert alert-danger">
                                    ${error.message}
                                </div>
                                <a href="/profile" data-link class="btn btn-primary">
                                    Volver a mi perfil
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
}
