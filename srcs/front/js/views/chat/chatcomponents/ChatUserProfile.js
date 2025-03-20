export class ChatUserProfile {
    constructor(container) {
        this.container = container;
        this.modal = null;
        this.modalContent = null;
        this.lastData = null;
        this.initializeModal();
    }

    initializeModal() {
        // Crear el modal una sola vez
        this.modal = document.createElement('div');
        this.modal.id = 'cw-stats-modal';
        this.modal.className = 'cw-modal';
        
        this.modalContent = document.createElement('div');
        this.modalContent.className = 'cw-modal-content';
        this.modal.appendChild(this.modalContent);
        
        document.body.appendChild(this.modal);

        // Manejar cierre del modal
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.hideModal();
            }
        });

        // Prevenir propagación de clicks dentro del contenido
        this.modalContent.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }

    async fetchStats(playerId) {
        try {
            const response = await fetch(`/api/dashboard/player-stats-id/${playerId}/`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include'
            });
            
            if (!response.ok) throw new Error('Network response was not ok');
            
            const data = await response.json();
            this.lastData = data; // Guardar los datos
            return data; // Retornar los datos
        } catch (error) {
            console.error('Error fetching player stats:', error);
            return null;
        }
    }

    showModal(data) {
        if (!data || !data.stats || !data.games) {
            console.error('Datos inválidos para mostrar el modal');
            return;
        }

        const { stats, games } = data;
        
        // Seleccionar la imagen con prioridad usando los nuevos campos
        const profileImage = stats.profile_image || stats.fortytwo_image || stats.avatar;
        
        // Determinar rango basado en victorias
        const rank = this.getUserRank(stats.games_won);
        
        this.modalContent.innerHTML = `
            <div class="cw-modal-header">
                <div class="cw-profile-avatar-section">
                    <div class="cw-rank-badge ${rank.className}">
                        <i class="fas fa-${rank.icon}"></i>
                    </div>
                    <div class="cw-avatar-container">
                        <img src="${profileImage}" 
                             alt="${stats.username}" 
                             class="cw-profile-avatar"
                             onerror="this.src='${stats.avatar}'">
                    </div>
                    <div class="cw-profile-info">
                        <h2>${stats.username}</h2>
                        <span class="cw-rank-title">${rank.title}</span>
                    </div>
                </div>
                <button class="cw-close-modal" title="Cerrar">&times;</button>
            </div>
            <div class="cw-profile-tabs">
                <button class="cw-profile-tab active" data-tab="stats">
                    <i class="fas fa-chart-bar"></i> Estadísticas
                </button>
                <button class="cw-profile-tab" data-tab="history">
                    <i class="fas fa-history"></i> Historial
                </button>
            </div>
            <div class="cw-modal-body">
                <div class="cw-profile-content active" id="stats-tab">
                    <div class="cw-stats-grid">
                        <div class="cw-stat-box">
                            <i class="fas fa-gamepad stat-icon"></i>
                            <div>
                                <span class="cw-stat-value">${stats.games_played}</span>
                                <span class="cw-stat-label">Partidas Jugadas</span>
                            </div>
                        </div>
                        <div class="cw-stat-box">
                            <i class="fas fa-trophy stat-icon"></i>
                            <div>
                                <span class="cw-stat-value">${stats.games_won}</span>
                                <span class="cw-stat-label">Victorias</span>
                            </div>
                        </div>
                        <div class="cw-stat-box">
                            <i class="fas fa-percentage stat-icon"></i>
                            <div>
                                <span class="cw-stat-value">${stats.win_ratio.toFixed(1)}%</span>
                                <span class="cw-stat-label">Ratio de Victoria</span>
                            </div>
                        </div>
                        <div class="cw-stat-box">
                            <i class="fas fa-chart-line stat-icon"></i>
                            <div>
                                <span class="cw-stat-value">${stats.avg_points_per_game?.toFixed(1) || '0'}</span>
                                <span class="cw-stat-label">Promedio por Partida</span>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="cw-profile-content" id="history-tab">
                    <div class="cw-match-history">
                        ${games.map(game => `
                            <div class="cw-match-item">
                                <span class="cw-match-player">${game.player1}</span>
                                <span class="cw-match-score">${game.score_player1} - ${game.score_player2}</span>
                                <span class="cw-match-player">${game.player2}</span>
                                <span class="cw-match-date">${new Date(game.date).toLocaleDateString()}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
            <div class="cw-modal-footer">
                <button class="cw-close-btn">
                    <i class="fas fa-times"></i> Cerrar
                </button>
            </div>
        `;

        // Añadir manejo de tabs
        const tabs = this.modalContent.querySelectorAll('.cw-profile-tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                // Desactivar todas las tabs y contenidos
                tabs.forEach(t => t.classList.remove('active'));
                this.modalContent.querySelectorAll('.cw-profile-content').forEach(c => 
                    c.classList.remove('active')
                );
                
                // Activar la tab seleccionada
                tab.classList.add('active');
                const contentId = `${tab.dataset.tab}-tab`;
                this.modalContent.querySelector(`#${contentId}`).classList.add('active');
            });
        });

        // Mostrar modal
        this.modal.classList.add('show');

        // Configurar cierre
        const handleClose = (e) => {
            if (e.target === this.modal || e.target.classList.contains('cw-close-modal')) {
                this.hideModal();
                document.removeEventListener('click', handleClose);
            }
        };

        // Añadir listener para cerrar
        this.modalContent.querySelector('.cw-close-modal').onclick = this.hideModal.bind(this);
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') this.hideModal();
        });

        // Añadir listener para el nuevo botón de cerrar
        this.modalContent.querySelector('.cw-close-btn').onclick = () => this.hideModal();
    }

    getUserRank(victories) {
        if (victories >= 50) {
            return {
                icon: 'crown',
                title: 'Gran Maestro',
                className: 'cw-rank-grandmaster',
                description: '50+ victorias'
            };
        } else if (victories >= 25) {
            return {
                icon: 'fire',
                title: 'Pongista en Llamas',
                className: 'cw-rank-elite',
                description: '25+ victorias'
            };
        } else if (victories >= 10) {
            return {
                icon: 'bolt',
                title: 'Rayo del Ping Pong',
                className: 'cw-rank-veteran',
                description: '10+ victorias'
            };
        } else if (victories >= 5) {
            return {
                icon: 'star',
                title: 'Promesa del Pong',
                className: 'cw-rank-intermediate',
                description: '5+ victorias'
            };
        }
        return {
            icon: 'child',
            title: 'Novato Entusiasta',
            className: 'cw-rank-novice',
            description: 'Primeros pasos'
        };
    }

    positionModal(targetElement) {
        if (!targetElement) {
            console.error('No se proporcionó el elemento objetivo');
            return;
        }

        const buttonRect = targetElement.getBoundingClientRect();
        const screenWidth = window.innerWidth;
        const modalWidth = 300;
        const gap = 10;

        // Intentar posicionar a la derecha del botón primero
        let left = buttonRect.right + gap;
        
        // Si no hay espacio a la derecha, intentar a la izquierda
        if (left + modalWidth > screenWidth - gap) {
            left = Math.max(gap, buttonRect.left - modalWidth - gap);
        }

        let top = buttonRect.top;
        
        // Asegurarse de que no se salga por abajo
        const modalHeight = this.modalContent.offsetHeight || 400;
        if (top + modalHeight > window.innerHeight - gap) {
            top = Math.max(gap, window.innerHeight - modalHeight - gap);
        }

        // Ajustar la transformación según la posición
        const isOnLeft = left < buttonRect.left;
        this.modalContent.style.transformOrigin = 
            `${isOnLeft ? 'right' : 'left'} ${Math.abs(top - buttonRect.top) < 10 ? 'top' : 'center'}`;

        // Aplicar posición
        this.modalContent.style.left = `${left}px`;
        this.modalContent.style.top = `${top}px`;
    }

    hideModal() {
        this.modal.classList.remove('show');
    }
}