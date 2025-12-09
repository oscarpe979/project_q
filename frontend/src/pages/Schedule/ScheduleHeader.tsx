import React, { useState, useRef } from 'react';
import ReactDOM from 'react-dom';
import { ChevronDown, FileSpreadsheet, LogOut } from 'lucide-react';
import { VoyageSelector } from './components/VoyageSelector';
import { authService } from '../../services/authService';
import { Backdrop } from '../../components/UI/Backdrop';

interface ScheduleHeaderProps {
    user?: { name: string; role: string; username: string; venueName?: string } | null;
    currentVoyageNumber?: string;
    voyages?: { voyage_number: string; start_date: string; end_date: string }[];
    onVoyageSelect?: (voyageNumber: string) => void;
    onNewSchedule?: () => void;
    isModified?: boolean;
    isNewDraft?: boolean;
    undo?: () => void;
    redo?: () => void;
    canUndo?: boolean;
    canRedo?: boolean;
    onPublishClick: () => void;
    onDeleteClick: () => void;
    startDate?: string;
    onSearch?: (term: string) => void;
    onLoadMore?: () => void;
    isLoadingMore?: boolean;
    hasMore?: boolean;
}

export const ScheduleHeader: React.FC<ScheduleHeaderProps> = (props) => {
    const { user, currentVoyageNumber } = props;
    const [isViewOptionsOpen, setIsViewOptionsOpen] = useState(false);
    const [isExporting, setIsExporting] = useState(false);
    const viewOptionsRef = useRef<HTMLDivElement>(null);

    // Extract ship and venue from username
    const getHeaderInfo = () => {
        if (!user?.username) return { ship: '', venue: 'Venue Schedule' };
        const parts = user.username.split('_');
        const shipCode = parts[0]?.toUpperCase() || '';
        if (user.venueName) {
            return { ship: shipCode, venue: user.venueName };
        }
        return { ship: shipCode, venue: 'Venue Schedule' };
    };

    const { ship, venue } = getHeaderInfo();


    const handleExportClick = async () => {
        if (!currentVoyageNumber) {
            alert('No voyage selected to export.');
            return;
        }

        setIsExporting(true);
        try {
            const { ship, venue } = getHeaderInfo();
            const dateStr = props.startDate ? props.startDate.replace(/-/g, '.') : new Date().toISOString().split('T')[0].replace(/-/g, '.');
            const filename = `${ship} ${venue} Schedule - VY${currentVoyageNumber} - ${dateStr}.xlsx`;

            let fileHandle: any = null;

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
                        return;
                    }
                    console.error('File picker error:', err);
                }
            }

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
                const writable = await fileHandle.createWritable();
                await writable.write(blob);
                await writable.close();
            } else {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
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

    const handleMenuAction = (action: () => void) => {
        setIsViewOptionsOpen(false);
        action();
    };

    return (
        <header className="top-header glass-header">
            <div className="header-left">
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
                            onNewSchedule={props.onNewSchedule}
                            isNewDraft={props.isNewDraft}
                            onSearch={props.onSearch}
                            onLoadMore={props.onLoadMore}
                            isLoadingMore={props.isLoadingMore}
                            hasMore={props.hasMore}
                        />
                    ) : (
                        <h2 className="header-title">
                            {ship ? `${ship} ${venue}` : venue}
                        </h2>
                    )}
                </div>
            </div>

            <div className="header-right">
                <div className="dropdown view-options-container" ref={viewOptionsRef} style={{ zIndex: 110 }}>
                    <button
                        onPointerDown={() => {
                            // Toggle, but prevent default to avoid immediate focus loss if needed
                            // Actually standard button behavior is fine
                            setIsViewOptionsOpen(!isViewOptionsOpen);
                        }}
                        className={`view-options-btn ${isViewOptionsOpen ? 'active' : ''}`}
                    >
                        View Options
                        <ChevronDown
                            size={16}
                            className={`view-options-icon ${isViewOptionsOpen ? 'open' : ''}`}
                        />
                    </button>
                    {isViewOptionsOpen && ReactDOM.createPortal(
                        <div style={{ position: 'relative', zIndex: 9999 }}>
                            {/* Generic Backdrop */}
                            <Backdrop onClose={() => setIsViewOptionsOpen(false)} zIndex={9998} />
                            {/* Position the menu relative to the button (calculated or fixed) -> Simplified: CENTERED or Fixed for now? 
                                Actually, existing code relied on relative positioning. 
                                To use Portal, we need position state.
                                Let's calculate rect from viewOptionsRef.
                            */}
                            <div
                                className="dropdown-menu interactive-overlay"
                                style={{
                                    position: 'fixed',
                                    top: viewOptionsRef.current ? viewOptionsRef.current.getBoundingClientRect().bottom + 4 : 0,
                                    right: viewOptionsRef.current ? window.innerWidth - viewOptionsRef.current.getBoundingClientRect().right : 0,
                                    left: 'auto', // Override any default and prevent stretching
                                    minWidth: '200px',
                                    zIndex: 9999
                                }}
                            >
                                <MenuItem
                                    onClick={() => {
                                        if (props.onNewSchedule) {
                                            handleMenuAction(props.onNewSchedule);
                                        }
                                    }}
                                    icon={
                                        <div className={`new-schedule-icon ${props.isNewDraft ? 'draft' : 'active'}`}>
                                            <span className="new-schedule-plus">+</span>
                                        </div>
                                    }
                                    label="New Schedule"
                                    disabled={props.isNewDraft}
                                />
                                <MenuItem
                                    onClick={() => handleMenuAction(handleExportClick)}
                                    icon={<FileSpreadsheet size={16} />}
                                    label={isExporting ? "Exporting..." : "Export to Excel"}
                                    disabled={!currentVoyageNumber}
                                />
                                <div className="dropdown-divider"></div>
                                <MenuItem
                                    onClick={() => handleMenuAction(props.onDeleteClick)}
                                    icon={<LogOut size={16} />}
                                    label="Delete Schedule"
                                    danger
                                    disabled={!currentVoyageNumber}
                                />
                            </div>
                        </div>,
                        document.body
                    )}
                </div>
                <button
                    className="btn btn-primary publish-btn"
                    onClick={props.onPublishClick}
                    disabled={props.isNewDraft}
                >
                    Publish Schedule
                </button>
            </div >
        </header >
    );
};

const MenuItem = ({ icon, label, onClick, danger = false, disabled = false }: { icon: React.ReactNode, label: string, onClick: () => void, danger?: boolean, disabled?: boolean }) => {
    return (
        <button
            onClick={disabled ? undefined : onClick}
            disabled={disabled}
            className={`menu-item ${danger ? 'danger' : ''}`}
        >
            {icon}
            {label}
        </button>
    );
};
