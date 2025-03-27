class TournamentService {
    // Cambiamos la ruta base para que coincida con Django
    static API_URL = '/api/tournament';

    static async fetchPlayedTournaments() {
        const response = await fetch(`${this.API_URL}/played_tournaments/`);
        return response.json();
    }

    static async fetchPendingTournaments() {
        const response = await fetch(`${this.API_URL}/pending_tournaments/`);
        return response.json();
    }

    static async createTournament(data) {
        try {
            // Añadimos la barra final para que coincida con la URL de Django
            const response = await fetch(`${this.API_URL}/create_tournament/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    // Aseguramos el CSRF token
                    'X-CSRFToken': document.cookie.split('; ')
                        .find(row => row.startsWith('csrftoken='))
                        ?.split('=')[1]
                },
                credentials: 'include', // Importante para las cookies
                body: JSON.stringify({
                    name: data.name,
                    max_match_points: data.max_match_points,
                    number_of_players: data.number_of_players,
                    participants: data.participants
                })
            });

            if (!response.ok) {
                const contentType = response.headers.get("content-type");
                if (contentType && contentType.includes("application/json")) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || errorData.detail || 'Error al crear el torneo');
                } else {
                    throw new Error(`Error ${response.status}: ${response.statusText}`);
                }
            }

            return await response.json();
        } catch (error) {
            console.error('Error en createTournament:', error);
            throw error;
        }
    }

    static async getTournamentDetails(id) {
        console.log('Llamando a getTournamentDetails:', id);
        const response = await fetch(`${this.API_URL}/tournament_detail/${id}/`);
        
        if (!response.ok) {
            throw new Error(`Error al obtener detalles del torneo: ${response.status}`);
        }
        
        return response.json();
    }

    static async startTournament(id) {
        console.log('Llamando a startTournament:', id);
        const response = await fetch(`${this.API_URL}/start_tournament/${id}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.cookie.split('; ')
                    .find(row => row.startsWith('csrftoken='))
                    ?.split('=')[1]
            },
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error(`Error al iniciar torneo: ${response.status}`);
        }
        
        return response.json();
    }

    static async deleteTournament(id) {
        const response = await fetch(`${this.API_URL}/delete_tournament/${id}/`, {
            method: 'DELETE'
        });
        return response.json();
    }

    static async getMatchInfo(tournamentId, matchId) {
        // Cambiar la URL para que coincida con el endpoint correcto
        const response = await fetch(`${this.API_URL}/tournament_matches/${tournamentId}/`);
        const matches = await response.json();
        const match = matches.find(m => m.id === parseInt(matchId));
        if (!match) {
            throw new Error('Match not found');
        }
        return match;
    }

    static async startMatch(matchId, data) {
        try {
            console.log('Enviando datos de partida a startMatch:', { matchId, data });
            const response = await fetch(`${this.API_URL}/start_match/${matchId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.cookie.split('; ')
                        .find(row => row.startsWith('csrftoken='))
                        ?.split('=')[1]
                },
                credentials: 'include',
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();

            // Determinar el ganador del torneo después de guardar el partido
            if (result.message === 'Partida guardada correctamente' && data.tournament_id) {
                await this.determineTournamentWinner(data.tournament_id);
            }

            return result;
        } catch (error) {
            console.error('Error en startMatch:', error);
            throw error;
        }
    }

    static async startMatchNotification(matchId) {
        try {
            const response = await fetch(`${this.API_URL}/start_match_notification/${matchId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.cookie.split('; ')
                        .find(row => row.startsWith('csrftoken='))
                        ?.split('=')[1]
                },
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error(`Error al notificar inicio de partida: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error en startMatchNotification:', error);
            throw error;
        }
    }

    static async determineTournamentWinner(tournamentId) {
        if (!tournamentId) {
            console.error('No se proporcionó tournament_id');
            return;
        }

        try {
            console.log('Determinando ganador para torneo:', tournamentId);
            const response = await fetch(`${this.API_URL}/determine_winner/${tournamentId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.cookie.split('; ')
                        .find(row => row.startsWith('csrftoken='))
                        ?.split('=')[1]
                },
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error(`Error al determinar ganador: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error al determinar el ganador:', error);
            throw error;
        }
    }

    static async updateMatchResult(tournamentId, matchId, result) {
        try {
            console.log('Enviando resultado:', { tournamentId, matchId, result });
            const response = await fetch(`${this.API_URL}/start_match/${matchId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.cookie.split('; ')
                        .find(row => row.startsWith('csrftoken='))
                        ?.split('=')[1]
                },
                credentials: 'include',
                body: JSON.stringify({
                    player1Points: result.player1_points,
                    player2Points: result.player2_points,
                    winner_id: result.winner
                })
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.error('Error response:', errorText);
                throw new Error(`Error del servidor: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error en updateMatchResult:', error);
            throw error;
        }
    }

    static async getTournamentBracket(tournamentId) {
        try {
            const response = await fetch(`${this.API_URL}/tournament_bracket/${tournamentId}/`);
            return await response.json();
        } catch (error) {
            console.error('Error fetching tournament bracket:', error);
            throw error;
        }
    }
}

async function startMatch(matchId, matchData) {
    try {
        const response = await fetch(`/api/tournament/match/${matchId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(matchData)
        });

        if (!response.ok) {
            throw new Error('Error al actualizar el partido');
        }

        const data = await response.json();
        console.log('Respuesta del servidor para siguiente partida:', data); // Debug
        return data;
    } catch (error) {
        console.error('Error en startMatch:', error);
        throw error;
    }
}

async function getTournamentSummary(tournamentId) {
    try {
        const response = await fetch(`/api/tournaments/${tournamentId}/summary`);
        const data = await response.json();
        
        // Procesar y ordenar los jugadores por puntuación
        return data.players.sort((a, b) => b.totalPoints - a.totalPoints);
    } catch (error) {
        console.error('Error fetching tournament summary:', error);
        throw error;
    }
}

export default TournamentService;
