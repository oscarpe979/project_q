import React from 'react';
import { Calendar, Settings, Upload, LogOut, LayoutGrid } from 'lucide-react';
import clsx from 'clsx';

interface MainLayoutProps {
    children: React.ReactNode;
    onImportClick?: () => void;
    onLogout?: () => void;
    user?: { name: string; role: string; username: string } | null;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children, onImportClick, onLogout, user }) => {
    // Extract ship and venue from username (e.g., wn_studiob)
    const getHeaderInfo = () => {
        if (!user?.username) return { ship: '', venue: 'Venue Schedule' };

        const parts = user.username.split('_');
        const shipCode = parts[0]?.toUpperCase() || '';
        const venueCode = parts[1]?.toLowerCase() || '';

        const venueMap: Record<string, string> = {
            'studiob': 'Studio B',
            'theater': 'Royal Theater',
            'two70': 'Two70°',
            'aquatheater': 'AquaTheater',
            'music': 'Music Hall'
        };

        const venueName = venueMap[venueCode] || 'Venue';
        return { ship: shipCode, venue: venueName };
    };

    const { ship, venue } = getHeaderInfo();

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
                        <h1 style={{ fontSize: '1.25rem', fontWeight: 'bold', letterSpacing: '-0.025em' }}>VenueSched</h1>
                        <p style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', fontWeight: 500, letterSpacing: '0.05em', textTransform: 'uppercase' }}>Royal Caribbean</p>
                    </div>
                </div>

                {/* Navigation */}
                <nav className="nav-menu">
                    <div className="nav-section-label">Menu</div>
                    <NavItem icon={<Calendar size={20} />} label="Schedule" active />
                    <NavItem icon={<Upload size={20} />} label="Import Grid" onClick={onImportClick} />

                    <div style={{ marginTop: '1.5rem' }}>
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
                        <div style={{ flex: 1, minWidth: 0 }}>
                            <p style={{ fontSize: '0.875rem', fontWeight: 'bold', lineHeight: '1.2', margin: 0 }}>{user?.name || 'User'}</p>
                            <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '0px', marginBottom: 0 }}>Role: {user?.role?.toUpperCase() || 'STAFF'}</p>
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
                <header className="top-header glass-header">
                    <div>
                        <h2 className="header-title">
                            {ship ? `${ship} ${venue} - Venue Schedule` : venue}
                        </h2>
                        <p className="header-meta">
                            <span className="status-dot"></span>
                            Live Draft • Last saved just now
                        </p>
                    </div>

                    <div style={{ display: 'flex', gap: '1rem' }}>
                        <button className="btn btn-secondary">
                            View Options
                        </button>
                        <button className="btn btn-primary">
                            Publish Schedule
                        </button>
                    </div>
                </header>

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
            <span style={{ transition: 'transform 0.2s', transform: active ? 'scale(1.1)' : 'none' }}>{icon}</span>
            <span>{label}</span>
        </button>
    );
};
