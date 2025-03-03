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
        const response = await fetch(`${this.API_URL}/tournament_detail/${id}/`);
        return response.json();
    }

    static async startTournament(id) {
        const response = await fetch(`${this.API_URL}/start_tournament/${id}/`, {
            method: 'POST'
        });
        return response.json();
    }

    static async deleteTournament(id) {
        const response = await fetch(`${this.API_URL}/delete_tournament/${id}/`, {
            method: 'DELETE'
        });
        return response.json();
    }
}

export default TournamentService;
