export function getNavbarHTML(isAuthenticated = false, userInfo = null) {
    const logoHTML = `
        <svg class="logo me-2" width="32" height="32" viewBox="0 0 100 100">
            <rect x="10" y="40" width="10" height="20" fill="#fff">
                <animate attributeName="height" values="20;40;20" dur="1s" repeatCount="indefinite"/>
            </rect>
            <circle cx="50" cy="50" r="5" fill="#fff">
                <animate attributeName="cx" values="50;52;50" dur="0.5s" repeatCount="indefinite"/>
                <animate attributeName="cy" values="50;48;50" dur="0.5s" repeatCount="indefinite"/>
            </circle>
            <rect x="80" y="40" width="10" height="20" fill="#fff">
                <animate attributeName="height" values="40;20;40" dur="1s" repeatCount="indefinite"/>
            </rect>
        </svg>
        <span class="brand-text">Transcendence</span>
    `;

    if (isAuthenticated) {
        // Determinar la imagen de perfil (foto de perfil > foto de 42 > dicebear)
        const profileImage = userInfo?.profile_image || 
                           userInfo?.fortytwo_image || 
                           `https://api.dicebear.com/7.x/avataaars/svg?seed=${userInfo?.username}`;

        return `
            <nav class="navbar navbar-expand-lg navbar-dark bg-dark fixed-top">
                <div class="container">
                    <a class="navbar-brand d-flex align-items-center" href="/" data-link>
                        ${logoHTML}
                    </a>
                    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                        <span class="navbar-toggler-icon"></span>
                    </button>
                    <div class="collapse navbar-collapse" id="navbarNav">
                        <ul class="navbar-nav me-auto">
                            <li class="nav-item">
                                <a class="nav-link" href="/game" data-link>
                                    <i class="fas fa-play me-1"></i>Jugar
                                </a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="/leaderboard" data-link>
                                    <i class="fas fa-trophy me-1"></i>Clasificación
                                </a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="/chat" data-link>
                                    <i class="fas fa-comments me-1"></i>Chat
                                </a>
                            </li>
                        </ul>
                        <ul class="navbar-nav">
                            <li class="nav-item dropdown">
                                <a class="nav-link dropdown-toggle d-flex align-items-center gap-2" href="#" role="button" 
                                   data-bs-toggle="dropdown" aria-expanded="false">
                                    <img src="${profileImage}" 
                                         alt="Avatar" 
                                         class="rounded-circle" 
                                         width="32" 
                                         height="32"
                                         onerror="this.src='https://api.dicebear.com/7.x/avataaars/svg?seed=${userInfo?.username}'">
                                    <span>${userInfo?.username}</span>
                                </a>
                                <ul class="dropdown-menu dropdown-menu-end">
                                    <li class="px-3 py-2 d-flex align-items-center bg-dark-subtle">
                                        <img src="${profileImage}" 
                                             alt="Avatar" 
                                             class="rounded-circle me-2" 
                                             width="48" 
                                             height="48"
                                             onerror="this.src='https://api.dicebear.com/7.x/avataaars/svg?seed=${userInfo?.username}'">
                                        <div class="text-truncate">
                                            <div class="fw-bold">${userInfo?.username}</div>
                                            <small class="text-muted">Ver perfil</small>
                                        </div>
                                    </li>
                                    <li><hr class="dropdown-divider"></li>
                                    <li>
                                        <a class="dropdown-item" href="/profile" data-link>
                                            <i class="fas fa-user me-2"></i>Perfil
                                        </a>
                                    </li>
                                    <li>
                                        <a class="dropdown-item" href="/settings" data-link>
                                            <i class="fas fa-cog me-2"></i>Configuración
                                        </a>
                                    </li>
                                    <li>
                                        <a class="dropdown-item" href="/gdpr-settings" data-link>
                                            <i class="fas fa-shield-alt me-2"></i>Privacidad
                                        </a>
                                    </li>
                                    <li><hr class="dropdown-divider"></li>
                                    <li>
                                        <button class="dropdown-item text-danger" id="logoutBtn">
                                            <i class="fas fa-sign-out-alt me-2"></i>Cerrar Sesión
                                        </button>
                                    </li>
                                </ul>
                            </li>
                        </ul>
                    </div>
                </div>
            </nav>
        `;
    } else {
        return `
            <nav class="navbar navbar-expand-lg navbar-dark bg-dark fixed-top">
                <div class="container">
                    <a class="navbar-brand d-flex align-items-center" href="/" data-link>
                        ${logoHTML}
                    </a>
                    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                        <span class="navbar-toggler-icon"></span>
                    </button>
                    <div class="collapse navbar-collapse" id="navbarNav">
                        <ul class="navbar-nav ms-auto">
                            <li class="nav-item">
                                <a class="nav-link" href="/login" data-link>
                                    <i class="fas fa-sign-in-alt me-2"></i>Login
                                </a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="/register" data-link>
                                    <i class="fas fa-user-plus me-2"></i>Registro
                                </a>
                            </li>
                        </ul>
                    </div>
                </div>
            </nav>
        `;
    }
}
