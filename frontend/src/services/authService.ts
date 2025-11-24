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
    }
};
