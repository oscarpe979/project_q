import React from 'react';
import { Calendar, Settings, Upload, LogOut, LayoutGrid } from 'lucide-react';
import clsx from 'clsx';

interface MainLayoutProps {
    children: React.ReactNode;
    onImportClick?: () => void;
    onLogout?: () => void;
    user?: { name: string; role: string; username: string; venueName?: string } | null;
    onPublish?: (voyageNumber: string) => Promise<void>;
    onDelete?: (voyageNumber: string) => Promise<void>;
    currentVoyageNumber?: string;
}

export const MainLayout: React.FC<MainLayoutProps> = (props) => {
    const { children, onImportClick, onLogout, user, currentVoyageNumber } = props;
    // Extract ship and venue from username (e.g., wn_studiob)
    const getHeaderInfo = () => {
        if (!user?.username) return { ship: '', venue: 'Venue Schedule' };

        const parts = user.username.split('_');
        const shipCode = parts[0]?.toUpperCase() || '';

        // Use venueName from backend if available
        if (user.venueName) {
            return { ship: shipCode, venue: user.venueName };
        }

        // Fallback for users without venue assignation (e.g. power users)
        return { ship: shipCode, venue: 'Venue Schedule' };
    };

    const { ship, venue } = getHeaderInfo();
    const [isPublishModalOpen, setIsPublishModalOpen] = React.useState(false);
    const [isDeleteModalOpen, setIsDeleteModalOpen] = React.useState(false);
    const [voyageNumber, setVoyageNumber] = React.useState('');
    const [isPublishing, setIsPublishing] = React.useState(false);
    const [isDeleting, setIsDeleting] = React.useState(false);
    const [isViewOptionsOpen, setIsViewOptionsOpen] = React.useState(false);

    const handlePublishClick = () => {
        setIsPublishModalOpen(true);
    };

    const handleDeleteClick = () => {
        setIsDeleteModalOpen(true);
        setIsViewOptionsOpen(false);
    };

    const handlePublishConfirm = async () => {
        if (!voyageNumber.trim()) {
            alert('Please enter a Voyage Number');
            return;
        }

        if (props.onPublish) {
            setIsPublishing(true);
            try {
                await props.onPublish(voyageNumber);
                setIsPublishModalOpen(false);
                setVoyageNumber('');
            } catch (error) {
                console.error(error);
                alert('Failed to publish schedule');
            } finally {
                setIsPublishing(false);
            }
        }
    };

    const handleDeleteConfirm = async () => {
        if (!voyageNumber.trim()) {
            alert('Please enter a Voyage Number to delete');
            return;
        }

        if (props.onDelete) {
            setIsDeleting(true);
            try {
                await props.onDelete(voyageNumber);
                setIsDeleteModalOpen(false);
                setVoyageNumber('');
            } catch (error) {
                console.error(error);
                alert('Failed to delete schedule');
            } finally {
                setIsDeleting(false);
            }
        }
    };

    // ... (rest of handlers)

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
                        <div className="dropdown" style={{ position: 'relative', display: 'inline-block' }}>
                            <button
                                className="btn btn-secondary"
                                onClick={() => setIsViewOptionsOpen(!isViewOptionsOpen)}
                            >
                                View Options
                            </button>
                            {isViewOptionsOpen && (
                                <div className="dropdown-content" style={{
                                    position: 'absolute',
                                    right: 0,
                                    top: '100%',
                                    marginTop: '0.5rem',
                                    backgroundColor: 'white',
                                    minWidth: '160px',
                                    boxShadow: '0px 4px 12px rgba(0,0,0,0.1)',
                                    zIndex: 10,
                                    padding: '0.5rem',
                                    borderRadius: '8px',
                                    border: '1px solid var(--border-color)'
                                }}>
                                    <button
                                        onClick={handleDeleteClick}
                                        style={{
                                            color: 'var(--error)',
                                            width: '100%',
                                            textAlign: 'left',
                                            border: 'none',
                                            background: 'none',
                                            cursor: 'pointer',
                                            padding: '0.5rem 0.75rem',
                                            borderRadius: '4px',
                                            fontSize: '0.875rem',
                                            fontWeight: 500,
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '0.5rem'
                                        }}
                                        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--bg-secondary)'}
                                        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                                    >
                                        <LogOut size={14} />
                                        Delete Schedule
                                    </button>
                                </div>
                            )}
                        </div>
                        <button className="btn btn-primary" onClick={handlePublishClick}>
                            Publish Schedule
                        </button>
                    </div>
                </header>

                {/* Scrollable Content */}
                <div className="workspace-card">
                    {children}
                </div>
            </main>

            {/* Publish Modal */}
            {isPublishModalOpen && (
                <div className="modal-overlay">
                    <div className="modal-content" style={{ width: '400px' }}>
                        <h3 style={{ marginBottom: '1rem' }}>Publish Schedule</h3>
                        <p style={{ marginBottom: '1rem', color: 'var(--text-secondary)' }}>Enter the Voyage Number to publish this schedule.</p>
                        <input
                            type="text"
                            placeholder="Voyage Number (e.g., WN-2025-11-17)"
                            value={voyageNumber}
                            onChange={(e) => setVoyageNumber(e.target.value)}
                            style={{ width: '100%', padding: '0.5rem', marginBottom: '1rem', borderRadius: '4px', border: '1px solid #ccc' }}
                        />
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                            <button className="btn btn-secondary" onClick={() => setIsPublishModalOpen(false)}>Cancel</button>
                            <button className="btn btn-primary" onClick={handlePublishConfirm} disabled={isPublishing}>
                                {isPublishing ? 'Publishing...' : 'Publish'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Delete Modal */}
            {isDeleteModalOpen && (
                <div className="modal-overlay">
                    <div className="modal-content" style={{ width: '400px' }}>
                        <h3 style={{ marginBottom: '1rem', color: 'red' }}>Delete Schedule</h3>
                        <p style={{ marginBottom: '1rem', color: 'var(--text-secondary)' }}>
                            You are about to delete the <strong>{currentVoyageNumber || 'current'}</strong> schedule.
                            <br />
                            Please confirm the Voyage Number to proceed.
                        </p>
                        <input
                            type="text"
                            placeholder="Voyage Number to Delete"
                            value={voyageNumber}
                            onChange={(e) => setVoyageNumber(e.target.value)}
                            style={{ width: '100%', padding: '0.5rem', marginBottom: '1rem', borderRadius: '4px', border: '1px solid #ccc' }}
                        />
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                            <button className="btn btn-secondary" onClick={() => setIsDeleteModalOpen(false)}>Cancel</button>
                            <button className="btn btn-primary" style={{ backgroundColor: 'red' }} onClick={handleDeleteConfirm} disabled={isDeleting}>
                                {isDeleting ? 'Deleting...' : 'Delete'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
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
