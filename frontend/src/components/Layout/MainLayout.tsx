import React from 'react';
import { Calendar, Settings, Upload, LogOut, LayoutGrid } from 'lucide-react';
import clsx from 'clsx';

interface MainLayoutProps {
    children: React.ReactNode;
    headerContent?: React.ReactNode;
    onImportClick?: () => void;
    onLogout?: () => void;
    user?: { name: string; role: string; username: string; venueName?: string } | null;
}

export const MainLayout: React.FC<MainLayoutProps> = (props) => {
    const { children, headerContent, onImportClick, onLogout, user } = props;

    return (
        <div className="app-container">
            {/* Sidebar */}
            <aside className="sidebar glass-panel">
                {/* Brand */}
                <div className="brand-section">
                    <div className="brand-icon">
                        <LayoutGrid size={20} strokeWidth={2.5} />
                    </div>
                    <div>
                        <h1 className="brand-title">VenueSched</h1>
                        <p className="brand-subtitle">Royal Caribbean</p>
                    </div>
                </div>

                {/* Navigation */}
                <nav className="nav-menu">
                    <div className="nav-section-label">Menu</div>
                    <NavItem icon={<Calendar size={20} />} label="Schedule" active />
                    <NavItem icon={<Upload size={20} />} label="Import Grid" onClick={onImportClick} />

                    <div className="nav-divider">
                        <div className="nav-section-label">System</div>
                        <NavItem icon={<Settings size={20} />} label="Settings" />
                    </div>
                </nav>

                {/* User Profile */}
                <div className="user-profile">
                    <div className="user-card">
                        <div className="user-avatar">
                            {user?.username ? user.username.split('_')[0].toUpperCase() : (user?.name.charAt(0) || 'U')}
                        </div>
                        <div className="user-info">
                            <p className="user-name">{user?.name || 'User'}</p>
                            <p className="user-role">Role: {user?.role?.toUpperCase() || 'STAFF'}</p>
                        </div>
                        <button
                            onClick={onLogout}
                            className="logout-btn"
                            title="Logout"
                        >
                            <LogOut size={20} />
                        </button>
                    </div>
                </div>
            </aside>

            {/* Main Content Area */}
            <main className="main-content">
                {/* Header */}
                {headerContent}

                {/* Scrollable Content */}
                <div className="workspace-card">
                    {children}
                </div>
            </main>
        </div>
    );
};

const NavItem = ({ icon, label, active = false, onClick }: { icon: React.ReactNode, label: string, active?: boolean, onClick?: () => void }) => {
    return (
        <button
            onClick={onClick}
            className={clsx("nav-item", active && "active")}
        >
            <span className="nav-icon-wrapper">{icon}</span>
            <span>{label}</span>
        </button>
    );
};
