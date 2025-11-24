export const authService = {
    setToken(token: string) {
        localStorage.setItem('access_token', token);
    },

    getToken(): string | null {
        return localStorage.getItem('access_token');
    },

    removeToken() {
        localStorage.removeItem('access_token');
    },

    getAuthHeaders(): HeadersInit {
        const token = this.getToken();
        return token ? { 'Authorization': `Bearer ${token}` } : {};
    },

    isAuthenticated(): boolean {
        return !!this.getToken();
    },

    async validateToken(): Promise<{ name: string; role: string; username: string } | null> {
        const token = this.getToken();
        if (!token) return null;

        try {
            const response = await fetch('http://localhost:8000/api/auth/me', {
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                this.removeToken();
                return null;
            }

            const userData = await response.json();
            return {
                name: userData.full_name,
                role: userData.role,
                username: userData.username
            };
        } catch (error) {
            console.error('Token validation failed:', error);
            this.removeToken();
            return null;
        }
    },

    logout() {
        this.removeToken();
    }
};
