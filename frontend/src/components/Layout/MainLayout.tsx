import React from 'react';
import { Calendar, Settings, Upload, LogOut, LayoutGrid } from 'lucide-react';
import clsx from 'clsx';

interface MainLayoutProps {
    children: React.ReactNode;
    onImportClick?: () => void;
    user?: { name: string; role: string };
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children, onImportClick, user }) => {
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
                            {user?.name.charAt(0) || 'U'}
                        </div>
                        <div style={{ flex: 1, minWidth: 0 }}>
                            <p style={{ fontSize: '0.875rem', fontWeight: 'bold', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{user?.name || 'User'}</p>
                            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{user?.role || 'Staff'}</p>
                        </div>
                        <LogOut size={18} style={{ color: 'var(--text-tertiary)' }} />
                    </div>
                </div>
            </aside>

            {/* Main Content Area */}
            <main className="main-content">
                {/* Header */}
                <header className="top-header glass-header">
                    <div>
                        <h2 className="header-title">Two70° Schedule</h2>
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
                <div style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
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
