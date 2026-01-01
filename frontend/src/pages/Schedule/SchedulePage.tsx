import { useState, useRef, useEffect } from 'react';
import { MainLayout } from '../../components/Layout/MainLayout';
import { ScheduleGrid } from './components/ScheduleGrid';
import { BaseModal } from '../../components/UI/BaseModal';
import { UnsavedChangesModal } from '../../components/UI/UnsavedChangesModal';
import { FileDropZone } from '../../components/Uploader/FileDropZone';
import { useScheduleState } from '../../hooks/useScheduleState';
import { authService } from '../../services/authService';
import { scheduleService } from '../../services/scheduleService';
import { useNavigate } from 'react-router-dom';
import { assignEventColors, getColorForType, COLORS } from '../../utils/eventColors';
import { ScheduleHeader } from './ScheduleHeader';
import { ScheduleModals } from './ScheduleModals';

// Helper to create a bright, light version of a color using HSL
const lightenColor = (hex: string, percent: number): string => {
    // Remove # and alpha if present
    const cleanHex = hex.replace('#', '').substring(0, 6);

    let r = parseInt(cleanHex.substr(0, 2), 16) / 255;
    let g = parseInt(cleanHex.substr(2, 2), 16) / 255;
    let b = parseInt(cleanHex.substr(4, 2), 16) / 255;

    // Convert RGB to HSL
    const max = Math.max(r, g, b), min = Math.min(r, g, b);
    let h = 0, s = 0, l = (max + min) / 2;

    if (max !== min) {
        const d = max - min;
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        switch (max) {
            case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
            case g: h = ((b - r) / d + 2) / 6; break;
            case b: h = ((r - g) / d + 4) / 6; break;
        }
    }

    // Make lighter but keep saturation high for vibrancy
    l = Math.min(0.85, l + percent);  // Increase lightness
    s = Math.min(1, s * 1.1);         // Slight saturation boost

    // Convert HSL back to RGB
    const hue2rgb = (p: number, q: number, t: number) => {
        if (t < 0) t += 1;
        if (t > 1) t -= 1;
        if (t < 1 / 6) return p + (q - p) * 6 * t;
        if (t < 1 / 2) return q;
        if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
        return p;
    };

    const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
    const p = 2 * l - q;
    r = hue2rgb(p, q, h + 1 / 3);
    g = hue2rgb(p, q, h);
    b = hue2rgb(p, q, h - 1 / 3);

    const toHex = (c: number) => Math.round(c * 255).toString(16).padStart(2, '0');
    return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
};

interface SchedulePageProps {
    user: { name: string; role: string; username: string; venueName?: string };
    onLogout: () => void;
}

export function SchedulePage({ user, onLogout }: SchedulePageProps) {
    const navigate = useNavigate();

    const {
        events,
        setEvents,
        itinerary,
        setItinerary,
        otherVenueShows,
        setOtherVenueShows,
        voyages,
        currentVoyageNumber,
        setCurrentVoyageNumber,
        isModified,
        setIsModified,
        isNewDraft,
        setIsNewDraft,
        historyIndex,
        history,
        loadSchedules,
        loadLatestSchedule,
        loadScheduleByVoyage,
        handleEventsChange,
        handleDateChange,
        handleLocationChange,
        handleTimeChange,
        handleOtherVenueShowUpdate,
        undo,
        redo,
        clearSchedule,
        setOriginalEvents,
        setOriginalItinerary,
        setOriginalOtherVenueShows,
        formatTimeDisplay,
        loadMoreSchedules,
        isLoadingMore,
        hasMore
    } = useScheduleState();

    const initialized = useRef(false);

    useEffect(() => {
        if (initialized.current) return;
        initialized.current = true;

        const loadData = async () => {
            try {
                await loadSchedules();
                await loadLatestSchedule();
            } catch (error) {
                console.error("Failed to load initial data", error);
            }
        };
        loadData();
    }, [loadSchedules, loadLatestSchedule]);

    // UI State
    const [isImportOpen, setIsImportOpen] = useState(false);
    const [isPublishSuccessOpen, setIsPublishSuccessOpen] = useState(false);
    const [isDeleteSuccessOpen, setIsDeleteSuccessOpen] = useState(false);

    // Modal State (moved from MainLayout)
    const [isPublishModalOpen, setIsPublishModalOpen] = useState(false);
    const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
    const [voyageNumberInput, setVoyageNumberInput] = useState('');
    const [isPublishing, setIsPublishing] = useState(false);
    const [publishError, setPublishError] = useState<string | undefined>(undefined);
    const [isPublishAsMode, setIsPublishAsMode] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);
    const [deleteError, setDeleteError] = useState<string | undefined>(undefined);

    const [isUploading, setIsUploading] = useState(false);
    const [uploadSuccess, setUploadSuccess] = useState(false);
    const [processingTime, setProcessingTime] = useState<string | null>(null);
    const abortControllerRef = useRef<AbortController | null>(null);

    // Unsaved Changes State
    const [isUnsavedModalOpen, setIsUnsavedModalOpen] = useState(false);
    const [pendingAction, setPendingAction] = useState<{ type: 'NEW' | 'LOAD' | 'LOGOUT', payload?: any } | null>(null);

    const handleFileSelect = async (file: File) => {
        setIsUploading(true);
        setUploadSuccess(false);
        setProcessingTime(null);
        const startTime = Date.now();
        const formData = new FormData();
        formData.append('file', file);

        const abortController = new AbortController();
        abortControllerRef.current = abortController;

        try {
            const headers = authService.getAuthHeaders();

            const response = await fetch('http://localhost:8000/api/upload/cd-grid', {
                method: 'POST',
                headers: headers,
                body: formData,
                signal: abortController.signal,
            });

            if (response.status === 401) {
                authService.removeToken();
                navigate('/login');
                throw new Error('Session expired. Please login again.');
            }

            if (!response.ok) throw new Error('Upload failed');

            const data = await response.json();

            // 1. Identify unique production shows to rotate colors
            const showTitles: string[] = [];
            data.events.forEach((e: any) => {
                if (e.type === 'show' && e.title && !showTitles.includes(e.title)) {
                    showTitles.push(e.title);
                }
            });

            const showColorMap: Record<string, string> = {};
            const showColors = [COLORS.PRODUCTION_SHOW_1, COLORS.PRODUCTION_SHOW_2, COLORS.PRODUCTION_SHOW_3];
            showTitles.forEach((title, index) => {
                showColorMap[title] = showColors[index % showColors.length];
            });

            // 2. Transform backend events to frontend format with rotated colors
            const newEvents = data.events.map((e: any, index: number) => {
                let color = getColorForType(e.type);
                if (e.type === 'show' && e.title && showColorMap[e.title]) {
                    color = showColorMap[e.title];
                }

                // Tech Runs inherit color from parent show (30% lighter)
                if (e.type === 'tech_run' && e.title) {
                    // Extract parent show from title (e.g., "Tech Run Voices" → "Voices")
                    for (const showTitle of showTitles) {
                        if (e.title.includes(showTitle)) {
                            // Lighten the color by 30%
                            const baseColor = showColorMap[showTitle];
                            color = lightenColor(baseColor, 0.3);
                            break;
                        }
                    }
                }

                return {
                    id: `imported-${Date.now()}-${index}`,
                    title: e.title,
                    start: new Date(e.start),
                    end: new Date(e.end),
                    color: color,
                    endIsLate: e.end_is_late || false,  // Pass Late flag from API
                    type: e.type
                };
            });

            // Transform and update itinerary
            if (data.itinerary && data.itinerary.length > 0) {
                const newItinerary = data.itinerary.map((day: any) => ({
                    day: day.day_number,
                    date: day.date,
                    location: day.port,
                    time: formatTimeDisplay(day.arrival_time, day.departure_time),
                    arrival: (day.arrival_time && day.arrival_time.trim().toLowerCase() !== 'null') ? day.arrival_time : null,
                    departure: (day.departure_time && day.departure_time.trim().toLowerCase() !== 'null') ? day.departure_time : null
                }));
                setItinerary(newItinerary);
                setIsNewDraft(false);
            } else {
                setItinerary([]);
            }

            // Process other venue shows
            if (data.other_venue_shows && data.other_venue_shows.length > 0) {
                const grouped: { [key: string]: { date: string; title: string; time: string }[] } = {};
                data.other_venue_shows.forEach((show: any) => {
                    if (!grouped[show.venue]) grouped[show.venue] = [];
                    grouped[show.venue].push({
                        date: show.date,
                        title: show.title,
                        time: show.time
                    });
                });
                const newOtherShows = Object.keys(grouped).map(venue => ({
                    venue,
                    shows: grouped[venue]
                }));
                setOtherVenueShows(newOtherShows);
            } else {
                setOtherVenueShows([]);
            }

            // We need to merge events.
            setEvents(prev => {
                const combinedEvents = [...prev, ...newEvents];
                return assignEventColors(combinedEvents);
            });

            setUploadSuccess(true);
            const durationSeconds = Math.floor((Date.now() - startTime) / 1000);
            const mins = Math.floor(durationSeconds / 60);
            const secs = durationSeconds % 60;
            setProcessingTime(`${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`);
            setIsUploading(false);

        } catch (error: any) {
            if (error.name === 'AbortError') return;
            console.error('Error uploading file:', error);
            alert('Failed to upload file. Please try again.');
            setIsUploading(false);
        } finally {
            abortControllerRef.current = null;
        }
    };

    const handleCancelImport = () => {
        if (abortControllerRef.current) abortControllerRef.current.abort();
        setIsUploading(false);
        setUploadSuccess(false);
        setProcessingTime(null);
        setIsImportOpen(false);
    };

    const handleLogoutRequest = () => {
        if (isModified) {
            setPendingAction({ type: 'LOGOUT' });
            setIsUnsavedModalOpen(true);
            return;
        }
        onLogout();
    };

    const handlePublishClick = () => {
        setVoyageNumberInput(currentVoyageNumber || '');
        setPublishError(undefined);
        setIsPublishAsMode(false);
        setIsPublishModalOpen(true);
    };

    const handlePublishAsClick = () => {
        setVoyageNumberInput('');
        setPublishError(undefined);
        setIsPublishAsMode(true);
        setIsPublishModalOpen(true);
    };

    const handleDeleteClick = () => {
        setVoyageNumberInput('');
        setDeleteError(undefined);
        setIsDeleteModalOpen(true);
    };

    const handlePublishConfirm = async () => {
        if (!voyageNumberInput.trim()) {
            setPublishError('Please enter a Voyage Number');
            return;
        }

        // --- SAFE PUBLISH CHECKS (Frontend UX) ---
        // Backend raises 409, but we can give immediate feedback if we know the list.
        // In "Publish As" mode, check against ALL existing voyages (treat as new schedule)
        // In normal mode, allow the current voyage number (updating same schedule)
        const isCollision = isPublishAsMode
            ? voyages.some(v => v.voyage_number === voyageNumberInput)
            : voyages.some(v => v.voyage_number === voyageNumberInput && v.voyage_number !== currentVoyageNumber);

        if (isCollision) {
            setPublishError(`Voyage Number "${voyageNumberInput}" already exists. Cannot overwrite.`);
            return;
        }

        setIsPublishing(true);
        try {
            // Pass originalVoyageNumber only in normal mode (not Publish As)
            const originalVoyage = isPublishAsMode ? undefined : currentVoyageNumber;
            await scheduleService.publishSchedule(voyageNumberInput, events, itinerary, otherVenueShows, originalVoyage);

            setUploadSuccess(true);
            setCurrentVoyageNumber(voyageNumberInput);
            setOriginalEvents(events);
            setOriginalItinerary(itinerary);
            setOriginalOtherVenueShows(otherVenueShows);
            setIsModified(false);
            setIsPublishSuccessOpen(true);
            setIsPublishModalOpen(false);
            setVoyageNumberInput('');
            loadSchedules();
        } catch (error: any) {
            console.error("Failed to publish schedule", error);
            if (error.message && error.message.includes('already exists')) {
                setPublishError(error.message); // Display backend conflict message
            } else {
                alert('Failed to publish schedule. Please try again.');
            }
        } finally {
            setIsPublishing(false);
        }
    };

    const handleDeleteConfirm = async () => {
        if (!voyageNumberInput.trim()) {
            setDeleteError('Please enter a Voyage Number to delete');
            return;
        }

        if (voyageNumberInput !== currentVoyageNumber) {
            setDeleteError(`Voyage Number does not match. Please enter '${currentVoyageNumber}' to confirm deletion.`);
            return;
        }

        setIsDeleting(true);
        try {
            await scheduleService.deleteSchedule(voyageNumberInput);
            setIsDeleteSuccessOpen(true);
            setIsDeleteModalOpen(false);
            setVoyageNumberInput('');
            clearSchedule();
            loadSchedules();
        } catch (error) {
            console.error(error);
            alert('Failed to delete schedule');
        } finally {
            setIsDeleting(false);
        }
    };

    const handleNewSchedule = () => {
        if (isModified) {
            setPendingAction({ type: 'NEW' });
            setIsUnsavedModalOpen(true);
            return;
        }
        executeNewSchedule();
    };

    const executeNewSchedule = () => {
        clearSchedule();
        setIsNewDraft(true);
    };

    const handleLoadScheduleByVoyage = async (voyageNumber: string) => {
        if (isModified) {
            setPendingAction({ type: 'LOAD', payload: voyageNumber });
            setIsUnsavedModalOpen(true);
            return;
        }
        await loadScheduleByVoyage(voyageNumber);
    };

    const handlePublishAndProceed = async () => {
        if (!currentVoyageNumber) {
            setIsUnsavedModalOpen(false);
            setIsPublishModalOpen(true);
        } else {
            try {
                // We need to call publish directly here, but we need voyageNumber.
                // If currentVoyageNumber exists, we use it.
                await scheduleService.publishSchedule(currentVoyageNumber, events, itinerary, otherVenueShows);

                // Update state after publish
                setOriginalEvents(events);
                setOriginalItinerary(itinerary);
                setOriginalOtherVenueShows(otherVenueShows);
                setIsModified(false);
                loadSchedules();

                if (pendingAction?.type === 'NEW') executeNewSchedule();
                if (pendingAction?.type === 'LOAD') loadScheduleByVoyage(pendingAction.payload);
                setPendingAction(null);
                setIsUnsavedModalOpen(false);
            } catch (e) {
                console.error("Failed to publish schedule", e);
                alert('Failed to publish schedule. Please try again.');
            }
        }
    };

    const handleDiscardAndProceed = () => {
        if (pendingAction?.type === 'NEW') executeNewSchedule();
        if (pendingAction?.type === 'LOAD') loadScheduleByVoyage(pendingAction.payload);
        if (pendingAction?.type === 'LOGOUT') onLogout();
        setPendingAction(null);
        setIsUnsavedModalOpen(false);
        setIsModified(false);
    };

    return (
        <>
            <MainLayout
                onImportClick={() => {
                    setUploadSuccess(false);
                    setIsImportOpen(true);
                }}
                onLogout={handleLogoutRequest}
                user={user}
                headerContent={
                    <ScheduleHeader
                        user={user}
                        currentVoyageNumber={currentVoyageNumber}
                        voyages={voyages}
                        onVoyageSelect={handleLoadScheduleByVoyage}
                        onNewSchedule={handleNewSchedule}
                        isModified={isModified}
                        isNewDraft={isNewDraft}
                        undo={undo}
                        redo={redo}
                        canUndo={historyIndex > 0}
                        canRedo={historyIndex < history.length - 1}
                        onPublishClick={handlePublishClick}
                        onPublishAsClick={handlePublishAsClick}
                        onDeleteClick={handleDeleteClick}
                        startDate={itinerary.length > 0 ? itinerary[0].date : undefined}
                        onSearch={loadSchedules}
                        onLoadMore={loadMoreSchedules}
                        isLoadingMore={isLoadingMore}
                        hasMore={hasMore}
                    />
                }
            >
                <ScheduleGrid
                    events={events}
                    setEvents={handleEventsChange}
                    itinerary={itinerary}
                    onDateChange={handleDateChange}
                    onLocationChange={handleLocationChange}
                    onTimeChange={handleTimeChange}
                    otherVenueShows={otherVenueShows}
                    onOtherVenueShowUpdate={handleOtherVenueShowUpdate}
                    isNewDraft={isNewDraft}
                    onImportClick={() => {
                        setUploadSuccess(false);
                        setProcessingTime(null);
                        setIsUploading(false);
                        setIsImportOpen(true);
                    }}
                    onStartClick={() => setIsNewDraft(false)}
                />
            </MainLayout>

            <ScheduleModals
                isPublishModalOpen={isPublishModalOpen}
                setIsPublishModalOpen={setIsPublishModalOpen}
                isDeleteModalOpen={isDeleteModalOpen}
                setIsDeleteModalOpen={setIsDeleteModalOpen}
                voyageNumber={voyageNumberInput}
                setVoyageNumber={setVoyageNumberInput}
                currentVoyageNumber={currentVoyageNumber}
                isPublishing={isPublishing}
                publishError={publishError}
                isDeleting={isDeleting}
                deleteError={deleteError}
                onPublishConfirm={handlePublishConfirm}
                onDeleteConfirm={handleDeleteConfirm}
                isPublishAsMode={isPublishAsMode}
            />

            <UnsavedChangesModal
                isOpen={isUnsavedModalOpen}
                onPublish={handlePublishAndProceed}
                onDiscard={handleDiscardAndProceed}
                onCancel={() => {
                    setPendingAction(null);
                    setIsUnsavedModalOpen(false);
                }}
            />

            <BaseModal
                isOpen={isImportOpen}
                onClose={handleCancelImport}
                title="Import Schedule"
            >
                {uploadSuccess ? (
                    <div className="processing-status-container success">
                        <div className="success-icon-wrapper">
                            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" strokeLinecap="round" strokeLinejoin="round" />
                                <path d="M22 4L12 14.01l-3-3" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                        </div>
                        <h3 className="success-title">Import Successful!</h3>
                        <p className="success-message">
                            The grid has been successfully imported and processed.
                            {processingTime && <span style={{ display: 'block', marginTop: '8px', fontSize: '0.9em', opacity: 0.8 }}>Processed in {processingTime}</span>}
                        </p>
                        <button
                            className="view-schedule-btn"
                            onClick={() => {
                                setIsImportOpen(false);
                            }}
                        >
                            View Schedule
                        </button>
                    </div>
                ) : (
                    <FileDropZone
                        onFileSelect={handleFileSelect}
                        isLoading={isUploading}
                    />
                )}
            </BaseModal>

            <BaseModal
                isOpen={isPublishSuccessOpen}
                onClose={() => setIsPublishSuccessOpen(false)}
                title="Schedule Saved"
            >
                <div className="processing-status-container success">
                    <div className="success-icon-wrapper">
                        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" strokeLinecap="round" strokeLinejoin="round" />
                            <path d="M22 4L12 14.01l-3-3" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                    </div>
                    <h3 className="success-title">Schedule Saved!</h3>
                    <p className="success-message">
                        Schedule for <strong>Voyage {currentVoyageNumber}</strong> has been successfully saved.
                    </p>
                    <button
                        className="view-schedule-btn"
                        onClick={() => setIsPublishSuccessOpen(false)}
                    >
                        Continue
                    </button>
                </div>
            </BaseModal>

            <BaseModal
                isOpen={isDeleteSuccessOpen}
                onClose={() => setIsDeleteSuccessOpen(false)}
                title="Schedule Deleted"
            >
                <div className="processing-status-container success">
                    <div className="success-icon-wrapper" style={{ color: 'var(--error)', backgroundColor: '#fee2e2' }}>
                        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M3 6h18" strokeLinecap="round" strokeLinejoin="round" />
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                    </div>
                    <h3 className="success-title" style={{ color: 'var(--error)' }}>Schedule Deleted</h3>
                    <p className="success-message">
                        Schedule for <strong>Voyage {currentVoyageNumber}</strong> has been successfully deleted.
                    </p>
                    <button
                        className="view-schedule-btn"
                        onClick={() => setIsDeleteSuccessOpen(false)}
                        style={{ backgroundColor: 'var(--error)' }}
                    >
                        Close
                    </button>
                </div>
            </BaseModal>
        </>
    );
}
