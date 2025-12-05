import { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { LoginPage } from './pages/Login/LoginPage';
import { SchedulePage } from './pages/Schedule/SchedulePage';
import { ProtectedRoute } from './components/Auth/ProtectedRoute';
import { authService } from './services/authService';

function App() {
  const navigate = useNavigate();
  const [user, setUser] = useState<{ name: string; role: string; username: string; venueName?: string } | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const currentUser = await authService.validateToken();
      setUser(currentUser);
    } catch (error) {
      console.error("Auth check failed", error);
    } finally {
      setIsCheckingAuth(false);
    }
  };

  const handleLogout = () => {
    authService.logout();
    setUser(null);
    navigate('/login');
  };

  if (isCheckingAuth) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>Loading...</div>;
  }

  return (
    <div className="app-container">
      <Routes>
        <Route path="/login" element={
          user ? <Navigate to="/schedule" replace /> : <LoginPage onLogin={(u) => { setUser(u); }} />
        } />

        <Route path="/schedule" element={
          <ProtectedRoute user={user}>
            <SchedulePage user={user!} onLogout={handleLogout} />
          </ProtectedRoute>
        } />

        <Route path="/" element={<Navigate to="/schedule" replace />} />
      </Routes>
    </div>
  );
}

export default App;
