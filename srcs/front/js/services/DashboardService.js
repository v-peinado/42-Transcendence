
class DashboardService {
    static async getPlayerStats() {
        const response = await fetch('/api/dashboard/player-stats/', {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('Error fetching player stats');
        }
        
        return await response.json();
    }
}

export default DashboardService;
