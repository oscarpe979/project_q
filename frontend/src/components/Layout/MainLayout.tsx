import React from 'react';
import { Calendar, Settings, Upload, LogOut, LayoutGrid, ChevronDown, FileSpreadsheet } from 'lucide-react';
import clsx from 'clsx';
import { VoyageSelector } from './VoyageSelector';
import { authService } from '../../services/authService';

interface MainLayoutProps {
    children: React.ReactNode;
    onImportClick?: () => void;
    onLogout?: () => void;
    user?: { name: string; role: string; username: string; venueName?: string } | null;
    onPublish?: (voyageNumber: string) => Promise<void>;
    onDelete?: (voyageNumber: string) => Promise<void>;
    currentVoyageNumber?: string;
    voyages?: { voyage_number: string; start_date: string; end_date: string }[];
    onVoyageSelect?: (voyageNumber: string) => void;
    onNewSchedule?: () => void;
    isModified?: boolean;
    undo?: () => void;
    redo?: () => void;
    canUndo?: boolean;
    canRedo?: boolean;
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
    const [isExporting, setIsExporting] = React.useState(false);
    const [isViewOptionsOpen, setIsViewOptionsOpen] = React.useState(false);
    const viewOptionsRef = React.useRef<HTMLDivElement>(null);

    React.useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (viewOptionsRef.current && !viewOptionsRef.current.contains(event.target as Node)) {
                setIsViewOptionsOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    const handlePublishClick = () => {
        if (currentVoyageNumber) {
            setVoyageNumber(currentVoyageNumber);
        }
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

        // Check for duplicate voyage number
        const isDuplicate = props.voyages?.some(
            v => v.voyage_number === voyageNumber && v.voyage_number !== props.currentVoyageNumber
        );

        if (isDuplicate) {
            alert(`Voyage Number "${voyageNumber}" already exists. Please use a unique number.`);
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

    const handleExportClick = async () => {
        if (!currentVoyageNumber) {
            alert('No voyage selected to export.');
            return;
        }

        setIsExporting(true);
        try {
            // Generate filename locally to open picker immediately
            const { ship, venue } = getHeaderInfo();
            const dateStr = new Date().toISOString().split('T')[0].replace(/-/g, '');
            const filename = `${ship}_${venue.replace(/\s+/g, '_')}_${currentVoyageNumber}_${dateStr}.xlsx`;

            let fileHandle: any = null;

            // Try to open picker first if supported
            if ('showSaveFilePicker' in window) {
                try {
                    fileHandle = await (window as any).showSaveFilePicker({
                        suggestedName: filename,
                        types: [{
                            description: 'Excel File',
                            accept: { 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'] },
                        }],
                    });
                } catch (err: any) {
                    if (err.name === 'AbortError') {
                        setIsExporting(false);
                        return; // User cancelled
                    }
                    console.error('File picker error:', err);
                    // Continue to fallback
                }
            }

            // Fetch data
            const headers = authService.getAuthHeaders();
            const response = await fetch(`http://localhost:8000/api/schedules/${currentVoyageNumber}/export`, {
                method: 'GET',
                headers: headers,
            });

            if (!response.ok) {
                throw new Error('Export failed');
            }

            const blob = await response.blob();

            if (fileHandle) {
                // Write to selected file
                const writable = await fileHandle.createWritable();
                await writable.write(blob);
                await writable.close();
            } else {
                // Fallback download
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename; // Use locally generated name or from header if preferred
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            }

            setIsViewOptionsOpen(false);
        } catch (error) {
            console.error('Export error:', error);
            alert('Failed to export schedule.');
        } finally {
            setIsExporting(false);
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
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                        <div>
                            {props.voyages && props.onVoyageSelect ? (
                                <VoyageSelector
                                    voyages={props.voyages}
                                    currentVoyageNumber={currentVoyageNumber || ''}
                                    onSelect={props.onVoyageSelect}
                                    title={ship ? `${ship} ${venue}` : venue}
                                    status={!currentVoyageNumber ? 'draft' : props.isModified ? 'modified' : 'live'}
                                    undo={props.undo}
                                    redo={props.redo}
                                    canUndo={props.canUndo}
                                    canRedo={props.canRedo}
                                />
                            ) : (
                                <h2 className="header-title">
                                    {ship ? `${ship} ${venue}` : venue}
                                </h2>
                            )}
                        </div>
                    </div>

                    <div style={{ display: 'flex', gap: '1rem' }}>
                        <div className="dropdown" ref={viewOptionsRef} style={{ position: 'relative', display: 'inline-block' }}>
                            <button
                                onClick={() => setIsViewOptionsOpen(!isViewOptionsOpen)}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.5rem',
                                    padding: '0.5rem 1rem',
                                    background: isViewOptionsOpen ? 'rgba(0, 0, 0, 0.05)' : 'transparent',
                                    border: '1px solid transparent',
                                    borderRadius: '8px',
                                    fontSize: '0.875rem',
                                    fontWeight: 500,
                                    color: 'var(--text-primary)',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s ease'
                                }}
                                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(0, 0, 0, 0.05)'}
                                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = isViewOptionsOpen ? 'rgba(0, 0, 0, 0.05)' : 'transparent'}
                            >
                                View Options
                                <ChevronDown
                                    size={16}
                                    style={{
                                        transform: isViewOptionsOpen ? 'rotate(180deg)' : 'none',
                                        transition: 'transform 0.2s ease',
                                        color: 'var(--text-secondary)'
                                    }}
                                />
                            </button>
                            {isViewOptionsOpen && (
                                <div className="dropdown-content" style={{
                                    position: 'absolute',
                                    right: 0,
                                    top: 'calc(100% + 4px)',
                                    backgroundColor: 'white',
                                    minWidth: '200px',
                                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
                                    zIndex: 50,
                                    padding: '0.5rem',
                                    borderRadius: '8px',
                                    border: '1px solid rgba(0,0,0,0.05)',
                                    animation: 'fadeIn 0.1s ease-out'
                                }}>
                                    <MenuItem
                                        onClick={() => {
                                            if (props.onNewSchedule) {
                                                props.onNewSchedule();
                                                setIsViewOptionsOpen(false);
                                            }
                                        }}
                                        icon={
                                            <div style={{
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                width: '24px',
                                                height: '24px',
                                                borderRadius: '50%',
                                                background: '#e0e7ff',
                                                color: '#6366f1'
                                            }}>
                                                <span style={{ fontSize: '16px', lineHeight: 1, fontWeight: 'bold' }}>+</span>
                                            </div>
                                        }
                                        label="New Schedule"
                                    />
                                    <MenuItem
                                        onClick={handleExportClick}
                                        icon={<FileSpreadsheet size={16} />}
                                        label={isExporting ? "Exporting..." : "Export to Excel"}
                                    />
                                    <div style={{ height: '1px', backgroundColor: 'var(--border-color)', margin: '0.25rem 0' }}></div>
                                    <MenuItem
                                        onClick={handleDeleteClick}
                                        icon={<LogOut size={16} />}
                                        label="Delete Schedule"
                                        danger
                                    />
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

const MenuItem = ({ icon, label, onClick, danger = false }: { icon: React.ReactNode, label: string, onClick: () => void, danger?: boolean }) => {
    const [isHovered, setIsHovered] = React.useState(false);

    return (
        <button
            onClick={onClick}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            style={{
                color: danger ? 'var(--error)' : 'var(--text-primary)',
                width: '100%',
                textAlign: 'left',
                border: 'none',
                background: isHovered ? 'var(--bg-secondary)' : 'transparent',
                cursor: 'pointer',
                padding: '0.5rem 0.75rem',
                borderRadius: '4px',
                fontSize: '0.875rem',
                fontWeight: 500,
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                marginBottom: '0.25rem',
                transition: 'background-color 0.2s'
            }}
        >
            {icon}
            {label}
        </button>
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
