import { Navigate } from 'react-router-dom';

interface ProtectedRouteProps {
    user: { name: string; role: string; username: string } | null;
    children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ user, children }) => {
    if (!user) {
        return <Navigate to="/login" replace />;
    }

    return <>{children}</>;
};
