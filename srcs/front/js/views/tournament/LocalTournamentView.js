import AuthService from '../../services/AuthService.js';
import TournamentService from '../../services/TournamentService.js';
import { getNavbarHTML } from '../../components/Navbar.js';
import { ChatWidget } from '../../components/ChatWidget.js';
import { loadHTML } from '../../utils/htmlLoader.js';

export async function LocalTournamentView() {
    const app = document.getElementById('app');
    app.innerHTML = '';

    try {
        // Cargar navbar y template
        const [userInfo, template] = await Promise.all([
            AuthService.getUserProfile(),
            loadHTML('/views/tournament/templates/TournamentView.html')
        ]);

        app.innerHTML = await getNavbarHTML(true, userInfo);
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = template;
        app.appendChild(tempDiv.firstElementChild);

        // Inicializar elementos y event listeners
        const elements = {
            createBtn: document.querySelector('#tournament-create-btn'),
            modal: document.getElementById('tournament-modal'),
            overlay: document.getElementById('modal-overlay'),
            form: document.getElementById('tournament-form'),
            cancelBtn: document.getElementById('tournament-cancel'),
            playersSelect: document.getElementById('players'),
            playersContainer: document.getElementById('tournament-players'),
            pendingBtn: document.getElementById('tournaments-pending-btn'),
            pendingModal: document.getElementById('pending-modal'),
            pendingModalClose: document.getElementById('pending-modal-close'),
            pendingCount: document.querySelector('.count-badge')
        };

        // Event Listeners corregidos
        elements.createBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            toggleModal(true, elements);
        });

        elements.overlay.addEventListener('click', () => {
            toggleModal(false, elements);
            togglePendingModal(false, elements);
        });

        elements.cancelBtn.addEventListener('click', (e) => {
            e.preventDefault();
            toggleModal(false, elements);
        });

        elements.playersSelect.addEventListener('change', () => {
            updatePlayersFields(elements);
        });

        if (elements.form) {
            elements.form.addEventListener('submit', async (e) => {
                e.preventDefault();
                e.stopPropagation();
                // Eliminamos la línea que causa el error y simplemente llamamos a handleFormSubmit
                await handleFormSubmit(e, elements);
            });
        }

        // Event listeners para el modal de torneos pendientes
        elements.pendingBtn.addEventListener('click', () => {
            togglePendingModal(true, elements);
        });

        elements.pendingModalClose.addEventListener('click', () => {
            togglePendingModal(false, elements);
        });

        // Inicializar campos de jugadores
        updatePlayersFields(elements);

        // Añadir manejo de tabs
        const tabs = document.querySelectorAll('.tournaments-tabs .tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                // Remover active de todos los tabs
                tabs.forEach(t => t.classList.remove('active'));
                // Añadir active al tab clickeado
                tab.classList.add('active');
                
                // Mostrar contenido correspondiente
                const tabId = tab.dataset.tab;
                document.querySelectorAll('.tab-content').forEach(content => {
                    content.classList.remove('active');
                });
                document.getElementById(`tournaments-${tabId}`).classList.add('active');
            });
        });

        // Inicializar participantes
        updatePlayersFields(elements);
        
        // Cargar torneos iniciales
        await loadTournaments();

        // Inicializar chat widget si no existe
        if (!document.querySelector('.chat-widget-container')) {
            await ChatWidget.initialize();
        }

        // Efecto linterna mejorado - Actualizar este bloque
        const cards = document.querySelectorAll('.game-mode-card'); // Cambiado de .with-glow a .game-mode-card
        cards.forEach(card => {
            card.addEventListener('mousemove', (e) => {
                const rect = card.getBoundingClientRect();
                const x = ((e.clientX - rect.left) / card.clientWidth) * 100;
                const y = ((e.clientY - rect.top) / card.clientHeight) * 100;
                card.style.setProperty('--x', `${x}%`);
                card.style.setProperty('--y', `${y}%`);
            });
        });

    } catch (error) {
        console.error('Error al cargar la vista del torneo:', error);
        app.innerHTML = '<div class="alert alert-danger">Error al cargar la vista del torneo</div>';
    }
}

// Funciones auxiliares
function toggleModal(show, elements) {
    elements.modal.style.display = show ? 'block' : 'none';
    elements.overlay.style.display = show ? 'block' : 'none';
    
    if (!show) {
        elements.form.reset();
        updatePlayersFields(elements);
    }
}

function togglePendingModal(show, elements) {
    elements.pendingModal.style.display = show ? 'block' : 'none';
    elements.overlay.style.display = show ? 'block' : 'none';
}

function updatePlayersFields(elements) {
    const numPlayers = parseInt(elements.playersSelect.value);
    elements.playersContainer.innerHTML = '';

    // Crear filas de dos jugadores
    for (let i = 0; i < numPlayers; i += 2) {
        const row = document.createElement('div');
        row.className = 'form-row d-flex gap-3 mb-3';

        // Primer jugador de la fila
        const firstPlayerDiv = createPlayerField(i + 1);
        firstPlayerDiv.classList.add('flex-1');
        row.appendChild(firstPlayerDiv);

        // Segundo jugador de la fila (si existe)
        if (i + 1 < numPlayers) {
            const secondPlayerDiv = createPlayerField(i + 2);
            secondPlayerDiv.classList.add('flex-1');
            row.appendChild(secondPlayerDiv);
        }

        elements.playersContainer.appendChild(row);
    }
}

function createPlayerField(playerNumber) {
    const div = document.createElement('div');
    div.className = 'form-group';

    const label = document.createElement('label');
    label.className = 'form-label neon-text';
    label.htmlFor = `player${playerNumber}`;
    label.textContent = `Participante ${playerNumber}`;

    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'form-control custom-input';
    input.id = `player${playerNumber}`;
    input.name = `player${playerNumber}`;
    input.required = true;
    input.maxLength = 50;

    div.appendChild(label);
    div.appendChild(input);
    return div;
}

async function handleFormSubmit(e, elements) {
    e.preventDefault();
    
    try {
        const formData = {
            name: elements.form.querySelector('#tournamentName').value.trim(),
            max_match_points: parseInt(elements.form.querySelector('#maxPoints').value),
            number_of_players: parseInt(elements.playersSelect.value),
            participants: Array.from(elements.playersContainer.querySelectorAll('input'))
                .map(input => input.value.trim())
        };

        // Validaciones
        if (!formData.name) {
            throw new Error('El nombre del torneo es requerido');
        }

        if (formData.max_match_points < 1) {
            throw new Error('Los puntos para ganar deben ser mayor a 0');
        }

        if (formData.participants.some(p => !p)) {
            throw new Error('Todos los nombres de participantes son requeridos');
        }

        const submitButton = elements.form.querySelector('button[type="submit"]');
        if (submitButton) submitButton.disabled = true;

        try {
            const response = await TournamentService.createTournament(formData);
            if (response.message) {
                showNotification('Torneo creado exitosamente', 'success');
                toggleModal(false, elements);
                
                // Actualizar torneos y contador
                const [pending, played] = await Promise.all([
                    TournamentService.fetchPendingTournaments(),
                    TournamentService.fetchPlayedTournaments()
                ]);
                
                // Actualizar contador
                elements.pendingCount.textContent = pending.length;
                
                // Actualizar lista de torneos pendientes
                renderTournaments('pending', pending);
                renderTournaments('played', played);
            } else {
                throw new Error('Error inesperado al crear el torneo');
            }
        } finally {
            if (submitButton) submitButton.disabled = false;
        }
    } catch (error) {
        console.error('Error al crear torneo:', error);
        showNotification(error.message, 'error');
    }
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} notification`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }, 100);
}

async function loadTournaments() {
    try {
        const [pending, played] = await Promise.all([
            TournamentService.fetchPendingTournaments(),
            TournamentService.fetchPlayedTournaments()
        ]);

        // Verificar que el elemento existe antes de actualizarlo
        const pendingCountElement = document.querySelector('.count-badge');
        if (pendingCountElement) {
            pendingCountElement.textContent = pending.length;
        }
        
        renderTournaments('pending', pending);
        renderTournaments('played', played);
    } catch (error) {
        console.error('Error loading tournaments:', error);
    }
}

function renderTournaments(type, tournaments) {
    const containerId = type === 'pending' ? 'tournaments-pending-list' : 'tournaments-played';
    const container = document.getElementById(containerId);
    
    if (!container) {
        console.error(`Container ${containerId} not found`);
        return;
    }

    container.textContent = '';

    // Actualizar el subtítulo del modal con el contador
    if (type === 'pending') {
        const modalTitle = document.querySelector('#pending-modal .modal-title');
        modalTitle.innerHTML = `
            <i class="fas fa-hourglass-half me-2"></i>
            Torneos en Espera
            <div class="modal-subtitle">${tournaments.length} torneo${tournaments.length !== 1 ? 's' : ''} pendiente${tournaments.length !== 1 ? 's' : ''}</div>
        `;
    }

    if (tournaments.length === 0) {
        const emptyMessage = document.createElement('p');
        emptyMessage.className = 'tournament-text text-center py-3';
        emptyMessage.textContent = type === 'pending' ? 'No hay torneos en espera' : 'No hay torneos finalizados';
        container.appendChild(emptyMessage);
        return;
    }

    tournaments.forEach(tournament => {
        const item = document.createElement('div');
        item.className = 'pending-tournament-item';

        item.innerHTML = `
            <div class="header">
                <div class="title-section">
                    <h3 class="title">${tournament.name}</h3>
                    <div class="tournament-info">
                        <span class="info-badge">
                            <i class="fas fa-star"></i>
                            ${tournament.max_match_points} puntos para ganar
                        </span>
                        <span class="info-badge">
                            <i class="fas fa-users"></i>
                            ${tournament.participants.length} jugadores
                        </span>
                    </div>
                </div>
            </div>
            
            <div class="participants">
                <div class="participants-grid">
                    ${tournament.participants.map((participant, index) => `
                        <div class="participant">
                            <span class="participant-number">#${index + 1}</span>
                            <span class="participant-name">${participant.username}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <div class="actions">
                ${type === 'pending' ? `
                    <button class="game-button primary-sm start-tournament" data-id="${tournament.id}">
                        <i class="fas fa-play"></i>
                        Iniciar Torneo
                    </button>
                ` : ''}
                <button class="game-button danger-sm delete-tournament" data-id="${tournament.id}">
                    <i class="fas fa-trash"></i>
                    Eliminar
                </button>
            </div>
        `;

        // Añadir event listeners para los botones
        if (type === 'pending') {
            item.querySelector('.start-tournament').onclick = async () => {
                await TournamentService.startTournament(tournament.id);
                window.location.href = `/tournament/game/${tournament.id}`;
            };
        }

        item.querySelector('.delete-tournament').onclick = async () => {
            if (confirm('¿Estás seguro de eliminar este torneo?')) {
                await TournamentService.deleteTournament(tournament.id);
                await loadTournaments();
            }
        };

        container.appendChild(item);
    });
}