import { loadHTML } from '../../utils/htmlLoader.js';
import DashboardService from '../../services/DashboardService.js';
import AuthService from '../../services/AuthService.js';
import { ChatWidget } from '../../components/ChatWidget.js';
import { getNavbarHTML } from '../../components/Navbar.js';  // Añadir esta importación

async function DashboardView() {
    try {
        const app = document.getElementById('app');
        
        // Cargar HTML y obtener datos simultáneamente
        const [dashboardHtml, footerHtml, userInfo, statsData] = await Promise.all([
            loadHTML('/views/dashboard/DashboardView.html'),
            loadHTML('/views/components/Footer.html'),
            AuthService.getUserProfile(),
            DashboardService.getPlayerStats()
        ]);

        // Obtener el navbar procesado correctamente
        const navbarHtml = await getNavbarHTML(true, userInfo);

        // Limpiar y añadir contenido
        app.innerHTML = navbarHtml + dashboardHtml + footerHtml;

        // Actualizar avatar y nombre de usuario
        if (userInfo) {
            const profileImage = userInfo.profile_image || 
                               userInfo.fortytwo_image || 
                               `https://api.dicebear.com/7.x/avataaars/svg?seed=${userInfo.username}`;

            // Actualizar avatar en el dashboard y navbar
            const avatarElements = document.querySelectorAll('#userAvatar, #nav-profile-image, #nav-profile-image-large');
            avatarElements.forEach(img => {
                if (img) {
                    img.src = profileImage;
                    img.onerror = () => {
                        img.src = `https://api.dicebear.com/7.x/avataaars/svg?seed=${userInfo.username}`;
                    };
                }
            });

            // Actualizar nombre de usuario
            const usernameElements = document.querySelectorAll('#userName, #nav-username, #nav-username-large');
            usernameElements.forEach(el => {
                if (el) el.textContent = userInfo.username;
            });
        }

        // Actualizar estadísticas
        const { stats, games } = statsData;
        
        const updateWithAnimation = (elementId, value) => {
            const element = document.getElementById(elementId);
            if (element) {
                element.style.opacity = '0';
                setTimeout(() => {
                    element.textContent = value;
                    element.style.transition = 'opacity 0.3s ease-in';
                    element.style.opacity = '1';
                }, 100);
            }
        };

        // Función para determinar el rango del jugador basado en victorias
        const getRankIcon = (victories) => {
            if (victories >= 50) return { 
                icon: 'crown', 
                color: '#ffd700', 
                title: '¡Gran Maestro! 👑',
                description: '50+ victorias'
            };
            if (victories >= 25) return { 
                icon: 'fire', 
                color: '#ff4d4d', 
                title: 'Pongista en Llamas 🔥',
                description: '25+ victorias'
            };
            if (victories >= 10) return { 
                icon: 'bolt', 
                color: '#00bcd4', 
                title: 'Rayo del Ping Pong ⚡',
                description: '10+ victorias'
            };
            if (victories >= 5) return { 
                icon: 'star', 
                color: '#4caf50', 
                title: 'Promesa del Pong ⭐',
                description: '5+ victorias'
            };
            return { 
                icon: 'child', 
                color: '#9e9e9e', 
                title: 'Novato Entusiasta 🌱',
                description: 'Primeros pasos'
            };
        };

        // Actualizar valores con animación
        updateWithAnimation('gamesPlayed', stats.games_played);
        updateWithAnimation('gamesWon', stats.games_won);
        updateWithAnimation('winRatio', `${stats.win_ratio.toFixed(1)}%`);
        updateWithAnimation('gamesWonRatio', stats.games_won);
        updateWithAnimation('gamesTotalRatio', stats.games_played);
        
        // Actualizar la barra de progreso del ratio
        const ratioProgressBar = document.querySelector('.ratio-progress');
        if (ratioProgressBar) {
            // Asegurarnos de que empiece en 0
            ratioProgressBar.style.width = '0%';
            // Forzar un reflow
            ratioProgressBar.offsetHeight;
            
            // Actualizar al valor real después de un pequeño delay
            requestAnimationFrame(() => {
                ratioProgressBar.style.width = `${stats.win_ratio}%`;
            });
        }

        // Actualizar el anillo de ratio con animación suave
        const ratioRing = document.querySelector('.ratio-ring');
        if (ratioRing) {
            ratioRing.style.setProperty('--progress', '0%');
            setTimeout(() => {
                ratioRing.style.setProperty('--progress', `${stats.win_ratio}%`);
            }, 300);
        }

        // Actualizar el círculo de victoria
        const victoryRing = document.querySelector('.victory-ring');
        if (victoryRing) {
            setTimeout(() => {
                victoryRing.style.setProperty('--progress', `${stats.win_ratio}%`);
            }, 300);
        }
        
        // Mostrar icono según victorias
        const rankIcon = document.querySelector('.rank-icon');
        if (rankIcon) {
            const rank = getRankIcon(stats.games_won);
            rankIcon.innerHTML = `
                <i class="fas fa-${rank.icon}"></i>
                <span class="rank-title">${rank.title}</span>
                <span class="rank-description">${rank.description}</span>
            `;
            rankIcon.style.color = rank.color;
            setTimeout(() => {
                rankIcon.classList.add('show');
            }, 800);
        }

        // Mostrar corona si el ratio es superior al 40%
        const crown = document.querySelector('.crown-icon');
        if (crown && stats.win_ratio > 40) {
            setTimeout(() => {
                crown.classList.add('show');
            }, 500);
        }

        // Actualizar el anillo de progreso
        const avatarProgress = document.querySelector('.avatar-progress');
        if (avatarProgress) {
            setTimeout(() => {
                avatarProgress.style.setProperty('--progress', `${stats.win_ratio}%`);
            }, 300); // Pequeño delay para la animación
        }

        updateWithAnimation('avgPoints', stats.avg_points_per_game.toFixed(1));
        updateWithAnimation('totalPoints', stats.total_points_scored);
        updateWithAnimation('pointsConceded', stats.total_points_conceded); // Añadimos esta línea

        // Variables para la paginación
        const GAMES_PER_PAGE = 3;
        let currentPage = 1;
        let totalPages = Math.ceil(games.length / GAMES_PER_PAGE);

        // Función para renderizar una página de juegos
        const renderGamesPage = (games, page) => {
            const start = (page - 1) * GAMES_PER_PAGE;
            const end = start + GAMES_PER_PAGE;
            const pageGames = games.slice(start, end);
            
            const gamesList = document.getElementById('gamesList');
            gamesList.innerHTML = '';

            pageGames.forEach((game, index) => {
                const row = document.createElement('tr');
                row.style.opacity = '0';
                
                const isWinner = game.winner === userInfo.username;
                const statusClass = isWinner ? 'victory' : 'defeat';
                
                row.innerHTML = `
                    <td class="match-date">
                        ${new Date(game.date).toLocaleDateString('es-ES', {
                            day: '2-digit',
                            month: 'short',
                            year: 'numeric'
                        })}
                    </td>
                    <td colspan="3">
                        <div class="match-result">
                            <span class="player-name">${game.player1}</span>
                            <span class="score">${game.score_player1} - ${game.score_player2}</span>
                            <span class="player-name">${game.player2}</span>
                        </div>
                    </td>
                    <td class="text-center">
                        <span class="match-status ${statusClass}">
                            ${isWinner ? 'Victoria' : 'Derrota'}
                        </span>
                    </td>
                `;
                
                gamesList.appendChild(row);
                
                setTimeout(() => {
                    row.style.transition = 'opacity 0.3s ease-in';
                    row.style.opacity = '1';
                }, 50 * index);
            });

            // Actualizar estado de los botones
            const prevButton = document.getElementById('prevPage');
            const nextButton = document.getElementById('nextPage');
            
            if (prevButton && nextButton) {
                prevButton.disabled = page <= 1;
                nextButton.disabled = page >= totalPages;
            }
        };

        // Inicializar paginación
        const initializePagination = () => {
            const prevButton = document.getElementById('prevPage');
            const nextButton = document.getElementById('nextPage');

            if (prevButton && nextButton) {
                prevButton.addEventListener('click', () => {
                    if (currentPage > 1) {
                        currentPage--;
                        renderGamesPage(games, currentPage);
                    }
                });

                nextButton.addEventListener('click', () => {
                    if (currentPage < totalPages) {
                        currentPage++;
                        renderGamesPage(games, currentPage);
                    }
                });
            }

            // Mostrar la primera página
            renderGamesPage(games, currentPage);
        };

        // Iniciar la paginación cuando se cambie a la pestaña de historial
        document.getElementById('history-tab').addEventListener('click', () => {
            setTimeout(() => {
                initializePagination();
            }, 100);
        });

        // Mostrar la primera página al cargar
        initializePagination();

        // Inicializar el chat widget después de cargar todo el contenido
        if (!document.querySelector('.chat-widget-container')) {
            await ChatWidget.initialize();
        }

    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

export { DashboardView };
