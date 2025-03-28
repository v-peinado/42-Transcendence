import AuthService from '../../services/AuthService.js';
import TournamentService from '../../services/TournamentService.js';
import { getNavbarHTML } from '../../components/Navbar.js';
import { ChatWidget } from '../../components/ChatWidget.js';
import { loadHTML } from '../../utils/htmlLoader.js';
import { soundService } from '../../services/SoundService.js';
import { TournamentGame } from '../../views/game/components/TournamentGame.js';
import TournamentModalService from '../../services/TournamentModalService.js';

export async function LocalTournamentView() {
    const app = document.getElementById('app');
    app.innerHTML = '';

    try {
        // Asegurarnos de que el CSS está cargado
        if (!document.querySelector('link[href="/css/tournament.css"]')) {
            const linkElem = document.createElement('link');
            linkElem.rel = 'stylesheet';
            linkElem.href = '/css/tournament.css';
            document.head.appendChild(linkElem);
        }

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
            form: document.getElementById('tournament-form'),
            playersSelect: document.getElementById('players'),
            playersContainer: document.getElementById('tournament-players'),
            pendingBtn: document.getElementById('tournaments-pending-btn'),
            pendingCount: document.querySelector('.count-badge')
        };

        // Remover funciones de modal y reemplazar por expansión de tarjetas
        elements.createBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            toggleCardExpansion(elements.createBtn);
        });

        elements.pendingBtn.addEventListener('click', () => {
            toggleCardExpansion(elements.pendingBtn);
        });

        elements.playersSelect.addEventListener('change', () => {
            updatePlayersFields(elements);
        });

        if (elements.form) {
            elements.form.addEventListener('submit', async (e) => {
                e.preventDefault();
                e.stopPropagation();
                await handleFormSubmit(e, elements);
            });

            // Botón cancelar
            const cancelButton = elements.form.querySelector('#tournament-cancel');
            if (cancelButton) {
                cancelButton.addEventListener('click', () => {
                    // Restablecer formulario
                    elements.form.reset();
                    updatePlayersFields(elements);
                    
                    // Contraer la tarjeta
                    const createCard = document.querySelector('#tournament-create-btn');
                    toggleCardExpansion(createCard); // Esto contraerá la tarjeta
                });
            }

            // Evitar que los clicks en el formulario cierren la tarjeta
            elements.form.addEventListener('click', (e) => {
                e.stopPropagation();
            });
        }

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

        // Añadir lógica para expandir/contraer tarjetas
        cards.forEach(card => {
            // Añadir botón de expandir
            const expandButton = document.createElement('button');
            expandButton.className = 'expand-button';
            expandButton.innerHTML = '<i class="fas fa-chevron-down"></i>';
            card.appendChild(expandButton);

            expandButton.addEventListener('click', (e) => {
                e.stopPropagation(); // Prevenir que el click se propague a la tarjeta
                toggleCardExpansion(card);
            });
        });

        function toggleCardExpansion(card) {
            const isExpanded = card.classList.contains('expanded');
            const expandButton = card.querySelector('.expand-button');
            const grid = card.closest('.game-modes-grid');
            
            if (isExpanded) {
                // Si ya está expandida, contraer
                card.classList.remove('expanded');
                if (expandButton) {
                    expandButton.innerHTML = '<i class="fas fa-chevron-down"></i>';
                }
                // Mostrar todas las tarjetas
                document.querySelectorAll('.game-mode-card').forEach(c => {
                    c.classList.remove('shrunk');
                });
                grid.classList.remove('has-expanded');
            } else {
                // Si no está expandida, expandir
                // Primero contraer todas
                document.querySelectorAll('.game-mode-card').forEach(c => {
                    c.classList.remove('expanded');
                    const btn = c.querySelector('.expand-button');
                    if (btn) btn.innerHTML = '<i class="fas fa-chevron-down"></i>';
                    if (c !== card) {
                        c.classList.add('shrunk');
                    }
                });
                
                // Luego expandir la seleccionada
                card.classList.add('expanded');
                if (expandButton) {
                    expandButton.innerHTML = '<i class="fas fa-chevron-up"></i>';
                }
                grid.classList.add('has-expanded');
            }
        }

        // Añadir event listener para el Salón de la Fama
        document.querySelector('#tournaments-finished').addEventListener('click', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            const card = document.querySelector('#tournaments-finished');
            
            // Primero expandir la tarjeta
            toggleCardExpansion(card);
            
            // Mostrar loader mientras se cargan los datos
            const container = document.getElementById('tournaments-finished-list');
            if (container) {
                container.innerHTML = `
                    <div class="text-center py-5">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Cargando torneos...</span>
                        </div>
                    </div>
                `;
            }
            
            // Pequeña espera para asegurar que la animación de expansión ha terminado
            await new Promise(resolve => setTimeout(resolve, 300));
            
            // Luego cargar los datos
            await loadFinishedTournaments();
        });

    } catch (error) {
        console.error('Error al cargar la vista del torneo:', error);
        app.innerHTML = '<div class="alert alert-danger">Error al cargar la vista del torneo</div>';
    }
}

// Funciones auxiliares
function updatePlayersFields(elements) {
    const container = elements.playersContainer;
    const form = elements.form;
    
    // Guardar la posición actual de scroll
    const formRect = form.getBoundingClientRect();
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const formTopRelative = formRect.top + scrollTop;
    
    // Actualizar contenido
    const numPlayers = parseInt(elements.playersSelect.value);
    container.innerHTML = '';

    // Procesar los jugadores en pares
    for (let i = 0; i < numPlayers; i += 2) {
        const rowDiv = document.createElement('div');
        rowDiv.className = 'players-row';
        
        // Si es el último jugador y es impar
        if (i === numPlayers - 1) {
            rowDiv.classList.add('odd-last');
            rowDiv.appendChild(createPlayerField(i + 1));
        } 
        // Si quedan dos jugadores (par)
        else {
            rowDiv.appendChild(createPlayerField(i + 1));
            if (i + 1 < numPlayers) {
                rowDiv.appendChild(createPlayerField(i + 2));
            }
        }
        
        container.appendChild(rowDiv);
    }

    // Asegurar que el scroll muestra el formulario completo
    const navbarHeight = 76; // altura del navbar
    const buffer = 20; // espacio extra
    const targetScroll = formTopRelative - navbarHeight - buffer;
    
    window.scrollTo({
        top: targetScroll,
        behavior: 'smooth'
    });
}

function createPlayerField(playerNumber) {
    const container = document.createElement('div');
    container.className = 'player-field-container';

    const label = document.createElement('label');
    label.className = 'form-label neon-text';
    label.htmlFor = `player${playerNumber}`;
    label.textContent = `Jugador ${playerNumber}`;

    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'player-field';
    input.id = `player${playerNumber}`;
    input.name = `player${playerNumber}`;
    input.required = true;
    input.maxLength = 50;
    input.placeholder = 'Nombre del jugador';

    // Mantener los event listeners existentes
    input.addEventListener('input', () => validatePlayerName(input));
    input.addEventListener('blur', () => validatePlayerName(input));

    container.appendChild(label);
    container.appendChild(input);

    return container;
}

function validatePlayerName(input) {
    const allInputs = document.querySelectorAll('.tournament-form input[type="text"]');
    const currentValue = input.value.trim().toLowerCase();
    let isDuplicate = false;

    allInputs.forEach(otherInput => {
        if (otherInput !== input && otherInput.value.trim().toLowerCase() === currentValue && currentValue !== '') {
            isDuplicate = true;
        }
    });

    if (isDuplicate) {
        input.setCustomValidity('Este nombre ya está en uso');
        input.classList.add('is-invalid');
        showInputError(input, 'Este nombre ya está en uso');
    } else {
        input.setCustomValidity('');
        input.classList.remove('is-invalid');
        hideInputError(input);
    }
}

function showInputError(input, message) {
    let errorDiv = input.nextElementSibling;
    if (!errorDiv || !errorDiv.classList.contains('invalid-feedback')) {
        errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        input.parentNode.insertBefore(errorDiv, input.nextSibling);
    }
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}

function hideInputError(input) {
    const errorDiv = input.nextElementSibling;
    if (errorDiv && errorDiv.classList.contains('invalid-feedback')) {
        errorDiv.style.display = 'none';
    }
}

async function handleFormSubmit(e, elements) {
    e.preventDefault();
    
    try {
        // Validar nombres duplicados antes de enviar
        const playerInputs = elements.form.querySelectorAll('input[type="text"]');
        const playerNames = new Set();
        let hasDuplicates = false;

        playerInputs.forEach(input => {
            const name = input.value.trim().toLowerCase();
            if (playerNames.has(name)) {
                hasDuplicates = true;
                input.setCustomValidity('Este nombre ya está en uso');
                showInputError(input, 'Este nombre ya está en uso');
            }
            playerNames.add(name);
        });

        if (hasDuplicates) {
            throw new Error('No pueden haber nombres duplicados');
        }

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

        const response = await TournamentService.createTournament(formData);
        
        if (response.message) {
            // 1. Contraer el formulario
            const createCard = document.querySelector('#tournament-create-btn');
            createCard.classList.remove('expanded');
            document.querySelectorAll('.game-mode-card').forEach(c => {
                c.classList.remove('shrunk');
            });
            createCard.closest('.game-modes-grid').classList.remove('has-expanded');
            
            // 2. Limpiar el formulario
            elements.form.reset();
            updatePlayersFields(elements);

            // 3. Actualizar la lista de torneos
            const pending = await TournamentService.fetchPendingTournaments();
            
            // 4. Actualizar el contador
            const countBadge = document.querySelector('.count-badge');
            if (countBadge) {
                countBadge.textContent = pending.length;
            }

            // 5. Renderizar los torneos pendientes con sus event listeners
            const pendingList = document.getElementById('tournaments-pending-list');
            if (pendingList) {
                pendingList.innerHTML = pending.length === 0 ? 
                    '<div class="text-center mt-3">No hay torneos pendientes</div>' :
                    pending.map(tournament => `
                        <div class="pending-tournament-item">
                            <div class="tournament-header">
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
                                <button class="expand-tournament-btn">
                                    <i class="fas fa-chevron-down"></i>
                                </button>
                            </div>
                            <div class="tournament-details" style="display: none;">
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
                                    <button class="game-button primary start-tournament" data-id="${tournament.id}">
                                        <i class="fas fa-play"></i>
                                        <span>Iniciar Torneo</span>
                                    </button>
                                    <button class="game-button danger delete-tournament" data-id="${tournament.id}">
                                        <i class="fas fa-trash"></i>
                                        <span>Eliminar Torneo</span>
                                    </button>
                                </div>
                            </div>
                        </div>
                    `).join('');

                // 6. Reinicializar los event listeners para la nueva lista
                pendingList.querySelectorAll('.pending-tournament-item').forEach(item => {
                    const header = item.querySelector('.tournament-header');
                    const expandBtn = item.querySelector('.expand-tournament-btn');
                    const details = item.querySelector('.tournament-details');
                    const startBtn = item.querySelector('.start-tournament');
                    const deleteBtn = item.querySelector('.delete-tournament');

                    const toggleDetailsOnly = (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        const isHidden = details.style.display === 'none';
                        details.style.display = isHidden ? 'block' : 'none';
                        expandBtn.classList.toggle('expanded');
                    };

                    header.addEventListener('click', toggleDetailsOnly);
                    expandBtn.addEventListener('click', toggleDetailsOnly);

                    if (startBtn) {
                        startBtn.addEventListener('click', (e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            handleStartTournament(startBtn.dataset.id);
                        });
                    }

                    if (deleteBtn) {
                        deleteBtn.addEventListener('click', (e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            handleDeleteTournament(deleteBtn.dataset.id);
                        });
                    }
                });
            }

            // 7. Mostrar notificación de éxito
            showNotification('Torneo creado con éxito', 'success');
        }
    } catch (error) {
        console.error('Error al crear torneo:', error);
        showNotification(error.message || 'Error al crear el torneo', 'error');
    } finally {
        const submitButton = elements.form.querySelector('button[type="submit"]');
        if (submitButton) submitButton.disabled = false;
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

        const pendingCountElement = document.querySelector('.count-badge');
        if (pendingCountElement) {
            pendingCountElement.textContent = pending.length;
        }

        const pendingList = document.getElementById('tournaments-pending-list');
        if (pendingList) {
            pendingList.innerHTML = pending.length === 0 ? 
                '<div class="text-center mt-3">No hay torneos pendientes</div>' :
                pending.map(tournament => `
                    <div class="pending-tournament-item">
                        <div class="tournament-header">
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
                            <button class="expand-tournament-btn">
                                <i class="fas fa-chevron-down"></i>
                            </button>
                        </div>
                        <div class="tournament-details" style="display: none;">
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
                                <button class="game-button primary start-tournament" data-id="${tournament.id}">
                                    <i class="fas fa-play"></i>
                                    <span>Iniciar Torneo</span>
                                </button>
                                <button class="game-button danger delete-tournament" data-id="${tournament.id}">
                                    <i class="fas fa-trash"></i>
                                    <span>Eliminar Torneo</span>
                                </button>
                            </div>
                        </div>
                    </div>
                `).join('');

            // Manejar expansión/contracción de cada torneo individual
            pendingList.querySelectorAll('.pending-tournament-item').forEach(item => {
                const header = item.querySelector('.tournament-header');
                const expandBtn = item.querySelector('.expand-tournament-btn');
                const details = item.querySelector('.tournament-details');

                const toggleDetailsOnly = (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    const isHidden = details.style.display === 'none';
                    details.style.display = isHidden ? 'block' : 'none';
                    expandBtn.classList.toggle('expanded');
                };

                header.addEventListener('click', toggleDetailsOnly);
                expandBtn.addEventListener('click', toggleDetailsOnly);
            });

            // Event listeners para los botones de acción
            pendingList.querySelectorAll('.start-tournament').forEach(button => {
                button.onclick = (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    handleStartTournament(button.dataset.id);
                };
            });

            pendingList.querySelectorAll('.delete-tournament').forEach(button => {
                button.onclick = (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    handleDeleteTournament(button.dataset.id);
                };
            });
        }
    } catch (error) {
        console.error('Error loading tournaments:', error);
        showNotification('Error al cargar los torneos', 'error');
    }
}

async function handleStartTournament(tournamentId) {
    try {
        // Primero iniciar el torneo para que envíe la notificación
        await TournamentService.startTournament(tournamentId);
        
        const tournamentDetails = await TournamentService.getTournamentDetails(tournamentId);
        const nextMatch = tournamentDetails.matches.find(match => !match.played);
        
        if (!nextMatch) {
            showNotification('No hay partidas pendientes en este torneo', 'error');
            return;
        }

        // Obtener match info
        const matchInfo = await TournamentService.getMatchInfo(tournamentId, nextMatch.id);
        const tournament = tournamentDetails;

        // Iniciar el juego
        await startMatch(matchInfo, tournament);
    } catch (error) {
        console.error('Error al iniciar el torneo:', error);
        showNotification('Error al iniciar el torneo', 'error');
    }
}

async function handleDeleteTournament(tournamentId) {
    if (confirm('¿Estás seguro de eliminar este torneo?')) {
        try {
            await TournamentService.deleteTournament(tournamentId);
            await loadTournaments();
            showNotification('Torneo eliminado exitosamente', 'success');
        } catch (error) {
            console.error('Error deleting tournament:', error);
            showNotification('Error al eliminar el torneo', 'error');
        }
    }
}

function renderTournaments(type, tournaments) {
    const containerId = type === 'pending' ? 'tournaments-pending-list' : 'tournaments-played';
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = '';

    if (tournaments.length === 0) {
        container.innerHTML = `<p class="text-center py-3">No hay torneos ${type === 'pending' ? 'pendientes' : 'finalizados'}</p>`;
        return;
    }

    tournaments.forEach(tournament => {
        const item = document.createElement('div');
        item.className = 'pending-tournament-item';
        item.innerHTML = `
            <div class="tournament-header">
                <div class="title-section">
                    <h3 class="title">
                        ${tournament.name}
                        <div class="tournament-info">
                            <span class="info-badge">
                                <i class="fas fa-trophy"></i>
                                ${tournament.max_match_points} puntos
                            </span>
                            <span class="info-badge">
                                <i class="fas fa-users"></i>
                                ${tournament.participants.length} jugadores
                            </span>
                            <span class="info-badge">
                                <i class="fas fa-gamepad"></i>
                                Local
                            </span>
                        </div>
                    </h3>
                </div>
            </div>
            <div class="participants-grid">
                ${tournament.participants.map((participant, index) => `
                    <div class="participant">
                        <span class="participant-number">#${(index + 1).toString().padStart(2, '0')}</span>
                        <span class="participant-name">${participant.username}</span>
                    </div>
                `).join('')}
            </div>
            <div class="actions">
                ${type === 'pending' ? `
                    <button class="game-button primary" data-id="${tournament.id}">
                        <i class="fas fa-play"></i>
                        <span>Iniciar Torneo</span>
                    </button>
                ` : ''}
                <button class="game-button danger" data-id="${tournament.id}">
                    <i class="fas fa-trash"></i>
                    <span>Eliminar Torneo</span>
                </button>
            </div>
        `;

        // Manejar el toggle de los detalles
        const header = item.querySelector('.tournament-header');
        const expandBtn = item.querySelector('.expand-tournament-btn');
        const details = item.querySelector('.tournament-details');

        const toggleDetails = () => {
            const isHidden = details.style.display === 'none';
            details.style.display = isHidden ? 'block' : 'none';
            expandBtn.classList.toggle('expanded', isHidden);
            expandBtn.querySelector('i').className = 'fas fa-chevron-down';
        };

        // Eventos de clic independientes
        [header, expandBtn].forEach(el => {
            el.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                toggleDetails();
            });
        });

        // Botón de inicio de torneo
        const startBtn = item.querySelector('.start-tournament');
        if (startBtn) {
            startBtn.onclick = (e) => {
                e.stopPropagation();
                handleStartTournament(tournament.id);
            };
        }

        // Botón de eliminar
        const deleteBtn = item.querySelector('.delete-tournament');
        if (deleteBtn) {
            deleteBtn.onclick = (e) => {
                e.stopPropagation();
                handleDeleteTournament(tournament.id);
            };
        }

        container.appendChild(item);
    });
}

// Añadir función para cargar torneos finalizados
async function loadFinishedTournaments() {
    try {
        const playedTournaments = await TournamentService.fetchPlayedTournaments();
        const container = document.getElementById('tournaments-finished-list');
        
        if (!container) return;

        // Eliminar la clase visible si existe
        container.classList.remove('visible');
        
        // Pequeña espera para asegurar que la transición funcione
        await new Promise(resolve => setTimeout(resolve, 50));

        if (playedTournaments.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-trophy"></i>
                    <p>No hay torneos finalizados todavía</p>
                </div>
            `;
        } else {
            container.innerHTML = `
                <div class="tournaments-grid">
                    ${playedTournaments.map(tournament => {
                        const winnerName = tournament.winner && tournament.winner.username 
                            ? tournament.winner.username 
                            : tournament.winner;

                        return `
                            <div class="tournament-card">
                                <h3 class="title">${tournament.name}</h3>
                                <div class="tournament-winner">
                                    <i class="fas fa-crown"></i>
                                    <span>${winnerName || 'Sin ganador'}</span>
                                </div>
                                <div class="participants">
                                    <div class="participants-grid">
                                        ${tournament.participants.map(p => `
                                            <div class="participant ${winnerName === p.username ? 'winner' : ''}">
                                                <span class="participant-name">${p.username}</span>
                                                ${winnerName === p.username ? '<i class="fas fa-crown"></i>' : ''}
                                            </div>
                                        `).join('')}
                                    </div>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            `;
        }

        // Añadir la clase visible para activar la transición
        requestAnimationFrame(() => {
            container.classList.add('visible');
        });

    } catch (error) {
        console.error('Error al cargar torneos finalizados:', error);
        showNotification('Error al cargar el historial de torneos', 'error');
    }
}

async function startMatch(match, tournament) {
    try {
        // Cargar templates
        const [gameTemplate, modalsTemplate, userInfo] = await Promise.all([
            loadHTML('/views/game/templates/GameMatch.html'),
            loadHTML('/views/tournament/templates/TournamentModals.html'),
            AuthService.getUserProfile()
        ]);

        // Primero notificar el inicio de partida antes de cargar la UI
        await TournamentService.startMatchNotification(match.id);

        const app = document.getElementById('app');
        app.innerHTML = await getNavbarHTML(true, userInfo);

        // Añadir el template del juego
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = gameTemplate;
        app.appendChild(tempDiv.firstElementChild);

        // Añadir todos los modales necesarios
        const modalsDiv = document.createElement('div');
        modalsDiv.innerHTML = modalsTemplate;
        app.appendChild(modalsDiv);

        // Verificar que todos los modales necesarios estén presentes
        const requiredModals = ['tournamentMatchFoundModal', 'tournamentGameOverScreen', 'tournamentSummaryModal'];
        requiredModals.forEach(modalId => {
            if (!document.getElementById(modalId)) {
                console.error(`Modal ${modalId} no encontrado en el DOM`);
            }
        });


        // Configurar el juego
        const canvas = document.getElementById('gameCanvas');
        canvas.width = 1000;
        canvas.height = 600;

        // Configurar la UI
        document.querySelector('#leftPlayerName').textContent = match.player1.username;
        document.querySelector('#rightPlayerName').textContent = match.player2.username;

        // Mostrar el modal inicial con los nombres correctos usando TournamentModalService
        TournamentModalService.showMatchStart(match.player1, match.player2);

        await new Promise(resolve => setTimeout(resolve, 2000));
        const matchFoundModal = document.getElementById('tournamentMatchFoundModal');
        if (matchFoundModal) matchFoundModal.style.display = 'none';

        // Mostrar countdown
        const countdown = document.getElementById('countdown');
        countdown.style.display = 'flex';
        
        for (let i = 3; i >= 1; i--) {
            countdown.textContent = i;
            countdown.classList.add('countdown-pulse');
            await soundService.playCountdown();
            await new Promise(r => setTimeout(r, 1000));
            countdown.classList.remove('countdown-pulse');
        }
        
        countdown.textContent = 'GO!';
        countdown.classList.add('countdown-pulse');
        await soundService.playCountdown();
        await new Promise(r => setTimeout(r, 1000));
        countdown.style.display = 'none';

        // Iniciar el juego
        const game = new TournamentGame(
            canvas,
            match,
            tournament.max_match_points,
            async (player1Points, player2Points, winner) => {
                game.stop();
                const matchData = {
                    player1Points: parseInt(player1Points),
                    player2Points: parseInt(player2Points),
                    winner_id: match[winner === 'Player1' ? 'player1' : 'player2'].id,
                    tournament_id: tournament.id
                };

                const result = await TournamentService.startMatch(match.id, matchData);
                await showResultModal(result, match, tournament, player1Points, player2Points, winner);
            }
        );

        game.start();

    } catch (error) {
        console.error('Error al iniciar partido:', error);
        window.location.href = '/tournament/local';
    }
}

async function showResultModal(result, match, tournament, player1Points, player2Points, winner) {
    try {
        // Obtener detalles actualizados del torneo
        const tournamentDetails = await TournamentService.getTournamentDetails(tournament.id);
        
        // Encontrar todos los partidos pendientes
        const pendingMatches = tournamentDetails.matches.filter(m => !m.winner);
        
        // Encontrar el siguiente partido (el primero pendiente)
        const nextMatch = pendingMatches.length > 0 ? pendingMatches[0] : null;

        console.log('Siguiente partido encontrado:', nextMatch);

        const buttons = [];
        
        if (nextMatch) {
            buttons.push({
                text: 'Siguiente Partido',
                onClick: async () => {
                    // Obtener los detalles del siguiente partido
                    try {
                        const matchInfo = await TournamentService.getMatchInfo(tournament.id, nextMatch.id);
                        // Iniciar directamente el siguiente partido
                        await startMatch(matchInfo, tournament);
                    } catch (error) {
                        console.error('Error al cargar siguiente partido:', error);
                        window.location.href = '/tournament/local';
                    }
                }
            });
        }

        buttons.push({
            text: 'Volver a Torneos',
            onClick: () => window.location.href = '/tournament/local#menu'
        });

        TournamentModalService.showGameOver({
            final_score: {
                player1: player1Points,
                player2: player2Points,
                player1_name: match.player1.username,
                player2_name: match.player2.username,
                tournament_id: tournament.id
            },
            winner: winner === 'Player1' ? match.player1.username : match.player2.username,
            nextMatch: nextMatch ? 
                `${nextMatch.player1.username} vs ${nextMatch.player2.username}` : 
                null,
            customButtons: buttons
        });

    } catch (error) {
        console.error('Error al mostrar resultado:', error);
        window.location.href = '/tournament/local';
    }
}