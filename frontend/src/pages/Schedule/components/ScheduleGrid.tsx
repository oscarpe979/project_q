import React, { useMemo, useState, useRef, useEffect, useCallback } from 'react';
import { format, addDays, startOfWeek, setMinutes, startOfDay } from 'date-fns';
import { DndContext, DragOverlay, useSensor, useSensors, PointerSensor } from '@dnd-kit/core';
import { NewDraftOverlay } from './NewDraftOverlay';
import { Edit2, Copy, Clipboard, Trash2 } from 'lucide-react';
import type { DragEndEvent, DragStartEvent, DragMoveEvent } from '@dnd-kit/core';
import { ContextMenu } from './ContextMenu';
import type { ContextMenuItem } from './ContextMenu';

import { TimeColumn } from './TimeColumn';
import { DayColumn } from './DayColumn';
import { EventBlock } from './EventBlock';
import { GhostEventOverlay } from './GhostEventOverlay';
import { DatePicker } from '../../../components/UI/DatePicker';
import { FooterHighlightCell } from './FooterHighlightCell';
import { PortTimeEditor } from './PortTimeEditor';
import type { Event, ItineraryItem, OtherVenueShow } from '../../../types';

interface ScheduleGridProps {
    events: Event[];
    setEvents: React.Dispatch<React.SetStateAction<Event[]>>;
    itinerary?: ItineraryItem[];
    onDateChange?: (dayIndex: number, newDate: Date) => void;
    onLocationChange?: (dayIndex: number, newLocation: string) => void;
    onTimeChange?: (dayIndex: number, arrival: string | null, departure: string | null) => void;
    otherVenueShows?: OtherVenueShow[];
    onOtherVenueShowUpdate?: (venue: string, date: string, title: string, time: string) => void;
    isNewDraft?: boolean;
    onImportClick?: () => void;
    onStartClick?: () => void;
}

const PIXELS_PER_HOUR = 100;
const START_HOUR = 7;
const SNAP_MINUTES = 5;
const HOURS_COUNT = 18; // 07:00 to 01:00 next day
const COLUMN_WIDTH_DEF = 'minmax(210px, 230px)';

interface DayHeaderCellProps {
    day: Date;
    info?: ItineraryItem;
    index: number;
    onDateChange?: (dayIndex: number, newDate: Date) => void;
    onLocationChange?: (dayIndex: number, newLocation: string) => void;
    onTimeChange?: (dayIndex: number, arrival: string | null, departure: string | null) => void;
}

const isAtSea = (location: string) => {
    const loc = location.toLowerCase().trim();
    return loc === 'at sea' || loc === 'cruising' || loc === 'sea day' || loc.includes('crossing') || loc.includes('passage');
};

const DayHeaderCell: React.FC<DayHeaderCellProps> = ({ day, info, index, onDateChange, onLocationChange, onTimeChange }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [isEditingLocation, setIsEditingLocation] = useState(false);
    const [isEditingTime, setIsEditingTime] = useState(false);
    const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
    const [activeTimeTab, setActiveTimeTab] = useState<'arrival' | 'departure'>('arrival');
    const [locationInput, setLocationInput] = useState(info ? info.location : '');
    const inputRef = useRef<HTMLInputElement>(null);
    const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    const onToggle = () => setIsOpen(!isOpen);

    // Helper to format 24h time to 12h for display
    const formatTo12Hour = (time: string | null | undefined) => {
        if (!time || time.trim().toLowerCase() === 'null') return '--:--';
        // If already has AM/PM, return as is
        if (time.match(/am|pm/i)) return time;

        const [h, m] = time.split(':');
        if (h === undefined || m === undefined) return time;

        let hour = parseInt(h, 10);
        const ampm = hour >= 12 ? 'PM' : 'AM';
        hour = hour % 12;
        hour = hour ? hour : 12;

        return `${hour}:${m} ${ampm}`;
    };

    useEffect(() => {
        if (info) {
            setLocationInput(info.location);
        }
    }, [info]);

    useEffect(() => {
        if (isEditingLocation && inputRef.current) {
            inputRef.current.focus();
        }
    }, [isEditingLocation]);

    useEffect(() => {
        return () => {
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
            }
        };
    }, []);

    const handleDateClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        onToggle();
    };

    const handleDateChange = (newDate: Date | null) => {
        if (newDate && onDateChange) {
            onDateChange(index, newDate);
        }
        if (isOpen) {
            onToggle();
        }
    };

    const handleLocationClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        setIsEditingLocation(true);
    };

    const handleLocationSubmit = () => {
        // Delay closing to allow "shrink back" animation (CSS transition is 0.05s)
        timeoutRef.current = setTimeout(() => {
            if (onLocationChange && locationInput !== (info ? info.location : '')) {
                onLocationChange(index, locationInput);
            }
            setIsEditingLocation(false);
        }, 50);
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') {
            e.currentTarget.blur(); // Triggers onBlur -> handleLocationSubmit
        } else if (e.key === 'Escape') {
            setLocationInput(info ? info.location : '');
            setIsEditingLocation(false);
        }
    };

    return (
        <div className="day-header-cell relative group">
            <div className="header-row-day-number">DAY {index + 1}</div>
            <div className="header-row-day-name">{format(day, 'EEEE')}</div>
            <div className="header-row-date relative group/date">
                {isOpen ? (
                    <input
                        type="text"
                        className="glass-input text-center cursor-pointer force-focus"
                        value={format(day, 'd-MMM-yy')}
                        readOnly
                        style={{ textTransform: 'none' }}
                        onClick={(e) => {
                            e.stopPropagation();
                            // Keep calendar open if clicking input
                        }}
                    />
                ) : (
                    <span
                        onDoubleClick={handleDateClick}
                        className={onDateChange ? "cursor-pointer select-none" : ""}
                        title="Double-click to change date"
                    >
                        {format(day, 'd-MMM-yy')}
                    </span>
                )}
                {onDateChange && (
                    <>
                        {!isOpen && (
                            <span className="pencil-spacer">
                                <span
                                    role="button"
                                    className="edit-icon-btn"
                                    onPointerDown={(e) => e.stopPropagation()}
                                    onClick={handleDateClick}
                                >
                                    <Edit2 size={10} className="edit-icon-svg" />
                                </span>
                            </span>
                        )}
                        {isOpen && (
                            <DatePicker
                                value={day}
                                onChange={handleDateChange}
                                onClose={onToggle}
                            />
                        )}
                    </>
                )}
            </div>
            <div className="header-row-location relative group/location">
                {isEditingLocation ? (
                    <input
                        ref={inputRef}
                        type="text"
                        className="glass-input"
                        value={locationInput}
                        onChange={(e) => setLocationInput(e.target.value)}
                        onBlur={handleLocationSubmit}
                        onKeyDown={handleKeyDown}
                        onClick={(e) => e.stopPropagation()}
                    />
                ) : (
                    <>
                        <span
                            onDoubleClick={handleLocationClick}
                            className={onLocationChange ? "cursor-pointer select-none" : ""}
                            title="Double-click to edit"
                        >
                            {info ? info.location : 'AT SEA'}
                        </span>
                        {onLocationChange && (
                            <span className="pencil-spacer">
                                <span
                                    role="button"
                                    className="edit-icon-btn"
                                    onPointerDown={(e) => e.stopPropagation()}
                                    onClick={handleLocationClick}
                                >
                                    <Edit2 size={10} className="edit-icon-svg" />
                                </span>
                            </span>
                        )}
                    </>
                )}
            </div>
            <div
                className={`header-row-time relative group/time ${!info?.time && !isAtSea(info?.location || '') ? 'opacity-50 hover:opacity-100 transition-opacity' : ''}`}
                ref={(el) => {
                    // Store ref for anchoring
                    if (el && isEditingTime && !anchorEl) {
                        setAnchorEl(el);
                    }
                }}
            >
                <div className="relative inline-flex items-center justify-center gap-1">
                    <span
                        onDoubleClick={(e) => {
                            if (isAtSea(info?.location || '')) return;
                            e.stopPropagation();
                            if (onTimeChange) {
                                setAnchorEl(e.currentTarget.closest('.header-row-time') as HTMLElement);
                                setIsEditingTime(true);
                                setActiveTimeTab('arrival'); // Reset to arrival on open
                            }
                        }}
                        className={onTimeChange && !isAtSea(info?.location || '') ? "cursor-pointer select-none" : ""}
                        title={isAtSea(info?.location || '') ? "" : "Double-click to edit times"}
                    >
                        {isEditingTime && info ? (
                            <>
                                <span style={{
                                    fontWeight: activeTimeTab === 'arrival' ? '800' : 'normal',
                                    color: activeTimeTab === 'arrival' ? '#1a73e8' : 'inherit'
                                }}>
                                    {formatTo12Hour(info.arrival)}
                                </span>
                                {' - '}
                                <span style={{
                                    fontWeight: activeTimeTab === 'departure' ? '800' : 'normal',
                                    color: activeTimeTab === 'departure' ? '#1a73e8' : 'inherit'
                                }}>
                                    {formatTo12Hour(info.departure)}
                                </span>
                            </>
                        ) : (
                            info?.time || (isAtSea(info?.location || '') ? '' : 'Add Time')
                        )}
                    </span>
                    {onTimeChange && !isEditingTime && !isAtSea(info?.location || '') && (
                        <span className="pencil-spacer">
                            <span
                                role="button"
                                className="edit-icon-btn"
                                onPointerDown={(e) => e.stopPropagation()}
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setAnchorEl(e.currentTarget.closest('.header-row-time') as HTMLElement);
                                    setIsEditingTime(true);
                                    setActiveTimeTab('arrival');
                                }}
                            >
                                <Edit2 size={10} className="edit-icon-svg" />
                            </span>
                        </span>
                    )}
                </div>
            </div>

            {/* M3 Port Time Editor Modal */}
            <PortTimeEditor
                isOpen={isEditingTime}
                onClose={() => {
                    setIsEditingTime(false);
                    setAnchorEl(null);
                }}
                onSave={(arrival, departure) => {
                    if (onTimeChange) {
                        onTimeChange(index, arrival, departure);
                    }
                }}
                initialArrival={info?.arrival || null}
                initialDeparture={info?.departure || null}
                portName={info?.location || 'Port Time'}
                anchorEl={anchorEl}
                onTabChange={setActiveTimeTab}
                activeTab={activeTimeTab}
            />
        </div>
    );
};

export const ScheduleGrid: React.FC<ScheduleGridProps> = ({
    events,
    setEvents,
    itinerary = [],
    onDateChange,
    onLocationChange,
    onTimeChange,
    otherVenueShows = [],
    onOtherVenueShowUpdate,
    isNewDraft,
    onImportClick,
    onStartClick,
}) => {
    // Context Menu State
    const [contextMenu, setContextMenu] = useState<{
        position: { x: number; y: number };
        type: 'event' | 'grid';
        data?: any;
    } | null>(null);

    // Clipboard State
    const [copiedEvent, setCopiedEvent] = useState<Event | null>(null);

    const handleUpdateEvent = useCallback((eventId: string, updates: { title?: string; timeDisplay?: string; color?: string }) => {
        setEvents(prev => prev.map(e => {
            if (e.id !== eventId) return e;
            return { ...e, ...updates } as Event;
        }));
    }, [setEvents]);

    const handleDeleteEvent = useCallback((eventId: string) => {
        setEvents(prev => prev.filter(e => e.id !== eventId));
    }, [setEvents]);

    const handleContextMenu = useCallback((e: React.MouseEvent, type: 'event' | 'grid', data?: any) => {
        e.preventDefault();
        e.stopPropagation();
        setContextMenu({
            position: { x: e.clientX, y: e.clientY },
            type,
            data
        });
    }, []);

    const handleCloseContextMenu = useCallback(() => {
        setContextMenu(null);
    }, []);

    const handleCopy = useCallback(() => {
        if (contextMenu?.type === 'event' && contextMenu.data) {
            const eventToCopy = events.find(e => e.id === contextMenu.data);
            if (eventToCopy) {
                setCopiedEvent(eventToCopy);
            }
        }
        handleCloseContextMenu();
    }, [contextMenu, events, handleCloseContextMenu]);

    const handlePaste = useCallback(() => {
        if (copiedEvent && contextMenu?.type === 'grid' && contextMenu.data && contextMenu.data.date) {
            const { date } = contextMenu.data; // y is relative clientY, need to map to time

            // We need to calculate the time based on the click position relative to the DayColumn
            // However, contextMenu.position is absolute clientX/Y.
            // We passed `y` (clientY) in the data payload from DayColumn's context menu handler if possible, 
            // OR we can use contextMenu.position.y if we have the rect of the column.

            // Simplification: In handleContextMenu for grid, we can calculate the time if we have the target element.
            // But managing refs for all columns here is hard.
            // Better approach: Calculate time inside the DayColumn's onContextMenu wrapper and pass it up.

            // Refined plan: DayColumn onContextMenu will calculate the time and pass it as data.

            const startHour = contextMenu.data.time || START_HOUR;
            const durationMs = copiedEvent.end.getTime() - copiedEvent.start.getTime();

            const newStart = new Date(date);
            const hours = Math.floor(startHour);
            const minutes = Math.round((startHour - hours) * 60);
            newStart.setHours(hours, minutes, 0, 0);

            const newEnd = new Date(newStart.getTime() + durationMs);

            const newEvent: Event = {
                ...copiedEvent,
                id: `copy-${Date.now()}`,
                start: newStart,
                end: newEnd,
                // Make sure we reset specific things if needed, but keeping color/title is desired
            };

            setEvents(prev => [...prev, newEvent]);
        }
        handleCloseContextMenu();
    }, [copiedEvent, contextMenu, handleCloseContextMenu, setEvents]);

    const contextMenuItems: ContextMenuItem[] = useMemo(() => {
        if (!contextMenu) return [];

        if (contextMenu.type === 'event') {
            return [
                {
                    label: 'Copy Event',
                    icon: <Copy size={16} />,
                    onClick: handleCopy
                },
                {
                    label: 'Delete Event',
                    icon: <Trash2 size={16} />,
                    onClick: () => {
                        if (contextMenu.data) handleDeleteEvent(contextMenu.data);
                    },
                    danger: true
                }
            ];
        }

        if (contextMenu.type === 'grid') {
            return [
                {
                    label: 'Paste Event',
                    icon: <Clipboard size={16} />,
                    onClick: handlePaste,
                    disabled: !copiedEvent
                }
            ];
        }

        return [];
    }, [contextMenu, copiedEvent, handleCopy, handlePaste, handleDeleteEvent]);


    const days = useMemo(() => {
        if (itinerary.length > 0) {
            return itinerary.map((item, index) => {
                if (!item.date) {
                    // Fallback for new drafts with empty dates
                    return addDays(new Date(), index);
                }
                const [year, month, day] = item.date.split('-').map(Number);
                const date = new Date(year, month - 1, day);
                return isNaN(date.getTime()) ? addDays(new Date(), index) : date;
            });
        }
        const startDate = startOfWeek(new Date(), { weekStartsOn: 1 });
        return Array.from({ length: 7 }, (_, i) => addDays(startDate, i));
    }, [itinerary]);

    const sensors = useSensors(
        useSensor(PointerSensor)
    );




    const handleDragEnd = (event: DragEndEvent) => {
        // Capture copy mode BEFORE resetting state - this reflects current Ctrl key state
        const isCopyMode = copyDragState.isCopyDrag;

        setCopyDragState(initialCopyDragState);

        const { active, delta, over } = event;

        const activeId = String(active.id);
        const isResizeBottom = activeId.endsWith('-resize-bottom');
        const isResizeTop = activeId.endsWith('-resize-top');
        const eventId = isResizeBottom
            ? activeId.replace('-resize-bottom', '')
            : isResizeTop
                ? activeId.replace('-resize-top', '')
                : activeId;

        setEvents((prev) => {
            const originalEvent = prev.find(e => e.id === eventId);
            if (!originalEvent) return prev;

            const minutesShift = delta.y * (60 / PIXELS_PER_HOUR);
            const snappedMinutes = Math.round(minutesShift / SNAP_MINUTES) * SNAP_MINUTES;

            let newStart = originalEvent.start;
            let newEnd = originalEvent.end;

            if (isResizeTop) {
                newStart = addDays(setMinutes(originalEvent.start, originalEvent.start.getMinutes() + snappedMinutes), 0);
                if (newStart >= originalEvent.end) return prev;
                const durationMinutes = (originalEvent.end.getTime() - newStart.getTime()) / (1000 * 60);
                if (durationMinutes < 15) {
                    newStart = new Date(originalEvent.end.getTime() - 15 * 60 * 1000);
                }
            } else if (isResizeBottom) {
                newEnd = addDays(setMinutes(originalEvent.end, originalEvent.end.getMinutes() + snappedMinutes), 0);
                if (newEnd <= originalEvent.start) return prev;
                const durationMinutes = (newEnd.getTime() - originalEvent.start.getTime()) / (1000 * 60);
                if (durationMinutes < 15) {
                    newEnd = new Date(originalEvent.start.getTime() + 15 * 60 * 1000);
                }
            } else {
                // Move
                newStart = addDays(setMinutes(originalEvent.start, originalEvent.start.getMinutes() + snappedMinutes), 0);
                newEnd = addDays(setMinutes(originalEvent.end, originalEvent.end.getMinutes() + snappedMinutes), 0);

                if (over && over.id !== activeId) {
                    const targetDayStr = String(over.id);
                    if (targetDayStr.includes('T')) {
                        const targetDay = new Date(targetDayStr);
                        const currentVisualDay = new Date(originalEvent.start);
                        if (currentVisualDay.getHours() < 4) {
                            currentVisualDay.setDate(currentVisualDay.getDate() - 1);
                        }
                        currentVisualDay.setHours(0, 0, 0, 0);
                        targetDay.setHours(0, 0, 0, 0);
                        const dayDiff = Math.round((targetDay.getTime() - currentVisualDay.getTime()) / (1000 * 60 * 60 * 24));

                        if (dayDiff !== 0) {
                            newStart = addDays(newStart, dayDiff);
                            newEnd = addDays(newEnd, dayDiff);
                        }
                    }
                }
            }

            // Check if changed
            if (newStart.getTime() === originalEvent.start.getTime() && newEnd.getTime() === originalEvent.end.getTime()) {
                return prev;
            }

            if (isCopyMode && !isResizeBottom && !isResizeTop) { // Only copy on move, not resize
                const newEvent = {
                    ...originalEvent,
                    id: `copy-${Date.now()}`,
                    start: newStart,
                    end: newEnd,
                    timeDisplay: undefined
                };
                return [...prev, newEvent];
            } else {
                // Normal update
                return prev.map(e => {
                    if (e.id === eventId) {
                        return {
                            ...e,
                            start: newStart,
                            end: newEnd,
                            timeDisplay: undefined
                        };
                    }
                    return e;
                });
            }
        });
    };

    // OPTIMIZATION: Pre-calculate layout and group by Visual Day
    // This removes O(Days * Events) complexity from the render loop and ensures stable props for Memoization.
    const eventsByDay = useMemo(() => {
        // 1. Calculate base layout (overlaps)
        const sortedEvents = [...events].sort((a, b) => {
            if (a.start.getTime() === b.start.getTime()) {
                // Sort by duration desc to optimize packing
                return (b.end.getTime() - b.start.getTime()) - (a.end.getTime() - a.start.getTime());
            }
            return a.start.getTime() - b.start.getTime();
        });

        // Note: This is a simplified packing algorithm. 
        // For full correctness with the previous logic, we can reuse the previous approach or assume simple column packing.
        // Replicating previous generic overlap logic:
        const eventsWithLayout = sortedEvents.map(event => {
            // Find overlapping events
            const overlapping = sortedEvents.filter(other =>
                other.id !== event.id &&
                other.start < event.end &&
                other.end > event.start
            );
            // Basic naive column visual (same as before)
            const totalOverlaps = overlapping.length + 1;
            // Better: count how many start before
            const predecessors = overlapping.filter(o => o.start.getTime() < event.start.getTime() || (o.start.getTime() === event.start.getTime() && o.id < event.id));
            const overlapIndex = predecessors.length;

            return {
                event,
                style: {
                    width: `${100 / totalOverlaps}%`,
                    left: `${(100 / totalOverlaps) * overlapIndex}%`
                }
            };
        });

        // 2. Group by Visual Day and Finalize Position
        const groups: Record<string, { event: Event; style: React.CSSProperties; isLate: boolean }[]> = {};

        eventsWithLayout.forEach(({ event, style: baseStyle }) => {
            const startHour = event.start.getHours() + event.start.getMinutes() / 60;

            // Determine Visual Day
            // If < 4am, it belongs to Previous Day visually (late night event)
            let visualDate: Date;
            let adjustedStartHour = startHour;

            if (startHour < 4) {
                visualDate = startOfDay(addDays(event.start, -1));
                adjustedStartHour += 24; // e.g. 1am -> 25h
            } else {
                visualDate = startOfDay(event.start);
            }

            const dayIso = visualDate.toISOString();
            if (!groups[dayIso]) groups[dayIso] = [];

            // Calculate Vertical Position using adjusted hour
            const top = (adjustedStartHour - START_HOUR) * PIXELS_PER_HOUR;
            const durationMinutes = (event.end.getTime() - event.start.getTime()) / (1000 * 60);
            let height = (durationMinutes / 60) * PIXELS_PER_HOUR;

            const maxGridHeight = HOURS_COUNT * PIXELS_PER_HOUR;
            let isLate = (top + height) > maxGridHeight;

            if (isLate) {
                height = Math.max(0, maxGridHeight - top);
            }

            // Final properties
            const finalItem = {
                event,
                isLate,
                style: {
                    ...baseStyle,
                    top: `${top}px`,
                    height: `${height}px`
                }
            };

            groups[dayIso].push(finalItem);
        });

        return groups;
    }, [events]);

    // OPTIMIZATION: Track day only in state. Track position via Refs to avoid re-renders.
    const [hoverDay, setHoverDay] = useState<string | null>(null);
    const highlightRefs = useRef<Map<string, HTMLDivElement>>(new Map());
    const ghostRefs = useRef<Map<string, HTMLDivElement>>(new Map());

    // Track creation drag via Ref (No re-renders)
    const activeCreationRef = useRef<{
        day: Date;
        startTop: number;
        currentTop: number
    } | null>(null);

    const isInteractionActive = () => {
        const active = document.activeElement;
        const isInput = active instanceof HTMLInputElement || active instanceof HTMLTextAreaElement;

        // Broad Safety Checks for Third-Party Libraries (MUI, etc.) and Generic Overlays
        const hasOpenExternalMenus = document.querySelector('.MuiPopper-root') || // MUI Date/Time Pickers, Selects
            document.querySelector('[role="dialog"]') ||    // Standard Modals
            document.querySelector('.interactive-overlay'); // Generic Class for our overlays

        return isInput || !!hasOpenExternalMenus;
    };

    const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>, day: Date) => {
        // 0. Ignore right-clicks (button 2) - let context menu handle them
        if (e.button !== 0) return;

        // 0.5. Close context menu if open and return (first click dismisses, doesn't start drag)
        if (contextMenu) {
            handleCloseContextMenu();
            return;
        }

        // 1. Click Protection
        // If an interaction is active (input focus, open menu), do NOT prevent default.
        // Let the click bubble so listeners can close the menus.
        if (isInteractionActive()) return;

        // 2. Prevent interference
        if ((e.target as HTMLElement).closest('.event-block')) return;

        e.preventDefault(); // ONLY prevent default if we're actually starting creation

        // 3. Start Creation
        const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
        const relativeY = e.clientY - rect.top;

        // Snap
        const hourOffset = relativeY / PIXELS_PER_HOUR;
        const totalMinutes = hourOffset * 60;
        const snappedMinutes = Math.floor(totalMinutes / SNAP_MINUTES) * SNAP_MINUTES;
        const snappedTop = (snappedMinutes / 60) * PIXELS_PER_HOUR;

        // Set Ref immediately
        activeCreationRef.current = {
            day,
            startTop: snappedTop,
            currentTop: snappedTop
        };

        // Show Ghost immediately via DOM
        const dayIso = day.toISOString();
        const ghostEl = ghostRefs.current.get(dayIso);

        if (ghostEl) {
            ghostEl.style.display = 'block';
            ghostEl.style.top = `${snappedTop}px`;
            ghostEl.style.height = '25px'; // Initial min height
            // Clear content initially or set to default
            const hintEl = ghostEl.querySelector('.ghost-drag-hint') as HTMLElement;
            const stdEl = ghostEl.querySelector('.ghost-standard-content') as HTMLElement;

            if (hintEl) hintEl.style.display = 'flex';
            if (stdEl) stdEl.style.display = 'none';

            // Start in "Line Mode"
            ghostEl.classList.add('is-initial-drag');
        }

        // Clear hover highlight
        setHoverDay(null);

        (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
    };

    // Consolidated Dnd Copy State
    interface CopyDragState {
        activeDragId: string | null;
        isCopyDrag: boolean;
        activeEvent: Event | null;
        eventHeight: string;
        eventWidth: number;
        delta: { x: number; y: number };
    }

    const initialCopyDragState: CopyDragState = {
        activeDragId: null,
        isCopyDrag: false,
        activeEvent: null,
        eventHeight: '50px',
        eventWidth: 210,
        delta: { x: 0, y: 0 },
    };

    const [copyDragState, setCopyDragState] = useState<CopyDragState>(initialCopyDragState);

    // Memoized event height lookup map
    const eventHeightMap = useMemo(() => {
        const map = new Map<string, string>();
        Object.values(eventsByDay).forEach(dayEvents => {
            dayEvents?.forEach(({ event, style }) => {
                map.set(event.id, style.height as string);
            });
        });
        return map;
    }, [eventsByDay]);

    const handleDragStart = (event: DragStartEvent) => {
        const activeId = String(event.active.id);
        const activatorEvent = event.activatorEvent as MouseEvent;
        const isCopyMode = activatorEvent.ctrlKey || activatorEvent.metaKey;

        // Find the event being dragged (skip resize handles)
        const eventId = activeId.replace('-resize-bottom', '').replace('-resize-top', '');
        const draggedEvent = events.find(e => e.id === eventId);

        // Get actual width from any event-box element (they all have same column width)
        const anyEventBox = document.querySelector('.event-box') as HTMLElement;
        const eventWidth = anyEventBox?.offsetWidth || 210;

        // Get height from memoized lookup map
        const eventHeight = draggedEvent ? eventHeightMap.get(draggedEvent.id) || '50px' : '50px';

        setCopyDragState({
            activeDragId: activeId,
            isCopyDrag: isCopyMode,
            activeEvent: draggedEvent || null,
            eventHeight,
            eventWidth,
            delta: { x: 0, y: 0 },
        });

        setHoverDay(null);
    };

    const handleDragMove = (event: DragMoveEvent) => {
        if (event.delta) {
            setCopyDragState(prev => ({ ...prev, delta: event.delta }));
        }
    };

    // Listen for Ctrl key press/release during drag to toggle copy mode
    useEffect(() => {
        if (!copyDragState.activeDragId) return;

        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Control' || e.key === 'Meta') {
                setCopyDragState(prev => ({ ...prev, isCopyDrag: true }));
            }
        };

        const handleKeyUp = (e: KeyboardEvent) => {
            if (e.key === 'Control' || e.key === 'Meta') {
                setCopyDragState(prev => ({ ...prev, isCopyDrag: false }));
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        window.addEventListener('keyup', handleKeyUp);
        return () => {
            window.removeEventListener('keydown', handleKeyDown);
            window.removeEventListener('keyup', handleKeyUp);
        };
    }, [copyDragState.activeDragId]);

    // Helper to format time
    const formatTimeDisplay = (h: number) => {
        const hr = Math.floor(h);
        const mn = Math.round((h - hr) * 60);
        const d = new Date(); d.setHours(hr, mn);
        return format(d, 'h:mm a');
    };

    const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>, day: Date) => {
        // Hide highlight if interaction (menu/input) is active
        if (isInteractionActive()) {
            if (hoverDay) setHoverDay(null);
            return;
        }

        e.preventDefault();

        if (copyDragState.activeDragId) {
            if (hoverDay) setHoverDay(null);
            return;
        }

        const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
        const relativeY = e.clientY - rect.top;

        const hourOffset = relativeY / PIXELS_PER_HOUR;
        const totalMinutes = hourOffset * 60;
        const snappedMinutes = Math.floor(totalMinutes / SNAP_MINUTES) * SNAP_MINUTES;
        const snappedTop = (snappedMinutes / 60) * PIXELS_PER_HOUR;

        if (activeCreationRef.current) {
            // Dragging behavior for NEW event (Ref based)
            const refState = activeCreationRef.current;
            if (day.getTime() !== refState.day.getTime()) return;

            // Update Ref
            refState.currentTop = snappedTop;

            // Calculate visual dimensions
            let top = Math.min(refState.startTop, refState.currentTop);
            let bottom = Math.max(refState.startTop, refState.currentTop);
            let height = bottom - top;

            if (height < 25) {
                height = 25;
                if (refState.currentTop < refState.startTop) {
                    top = refState.startTop - 25;
                } else {
                    top = refState.startTop;
                }
            }

            // Direct DOM Update
            const dayIso = day.toISOString();
            const ghostEl = ghostRefs.current.get(dayIso);
            if (ghostEl) {
                ghostEl.style.top = `${top}px`;
                ghostEl.style.height = `${height}px`;

                const startH = START_HOUR + (top / PIXELS_PER_HOUR);
                const endH = START_HOUR + ((top + height) / PIXELS_PER_HOUR);

                // Compact Mode Logic (match EventBlock < 50px)
                const isCompact = height < 50;
                if (isCompact) {
                    ghostEl.classList.add('is-compact');
                } else {
                    ghostEl.classList.remove('is-compact');
                }

                // Toggle Hint vs Standard
                const hintEl = ghostEl.querySelector('.ghost-drag-hint') as HTMLElement;
                const stdEl = ghostEl.querySelector('.ghost-standard-content') as HTMLElement;

                if (height < 15) {
                    ghostEl.classList.add('is-initial-drag'); // Line Mode
                    if (hintEl) hintEl.style.display = 'flex';
                    if (stdEl) stdEl.style.display = 'none';
                } else {
                    ghostEl.classList.remove('is-initial-drag'); // Box Mode
                    if (hintEl) hintEl.style.display = 'none';
                    if (stdEl) {
                        stdEl.style.display = 'flex';
                        stdEl.style.flexDirection = isCompact ? 'row' : 'column';
                        stdEl.style.gap = isCompact ? '4px' : '1px';
                    }
                }

                // Text Format: Compact = "Start", Normal = "Start - End"
                const timeText = isCompact
                    ? formatTimeDisplay(startH)
                    : `${formatTimeDisplay(startH)} - ${formatTimeDisplay(endH)}`;

                const contentEl = ghostEl.querySelector('.ghost-time');
                if (contentEl && contentEl.textContent !== timeText) {
                    contentEl.textContent = timeText;
                }
            }

        } else {
            // Hover logic - Optimized
            if ((e.target as HTMLElement).closest('.event-block')) {
                if (hoverDay) setHoverDay(null);
                return;
            }

            const dayIso = day.toISOString();

            // 1. Update React State only if Day changes
            if (hoverDay !== dayIso) {
                setHoverDay(dayIso);
            }

            // 2. Direct DOM update (ALWAYS update if ref exists)
            const el = highlightRefs.current.get(dayIso);
            if (el) {
                el.style.top = `${snappedTop}px`;
            }
        }
    };

    const handlePointerUp = (e: React.PointerEvent<HTMLDivElement>) => {
        e.preventDefault();

        if (!activeCreationRef.current) return;

        const { day, startTop, currentTop } = activeCreationRef.current;
        const dayIso = day.toISOString();

        // Hide Ghost ID
        const ghostEl = ghostRefs.current.get(dayIso);
        if (ghostEl) ghostEl.style.display = 'none';

        // Calculate final times
        let topY = Math.min(startTop, currentTop);
        let bottomY = Math.max(startTop, currentTop);
        let height = bottomY - topY;

        // Handle min height / click fallback
        // 15 mins = 25px
        // Handle min height / click fallback
        // Enforce "Drag to Create" -> Abort if movement is too small (click)
        if (height < 15) {
            // Was a click or tiny drag -> Cancel creation
            activeCreationRef.current = null;
            if (e.currentTarget.hasPointerCapture(e.pointerId)) {
                (e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId);
            }
            return;
        } else if (height < 25) {
            // Tiny drag but intentional: Force 15 mins standard
            height = 25;
            if (currentTop < startTop) {
                topY = startTop - 25;
            }
        }

        // Correct rounding for Start Time
        const startHourOffset = topY / PIXELS_PER_HOUR;
        const startTotalHours = START_HOUR + startHourOffset;
        const startH = Math.floor(startTotalHours);
        const startM = Math.round((startTotalHours - startH) * 60);

        const start = new Date(day);
        start.setHours(startH, startM, 0, 0);

        const durationHours = height / PIXELS_PER_HOUR;
        const durationMinutes = Math.round(durationHours * 60);
        const end = new Date(start.getTime() + durationMinutes * 60 * 1000);

        const newEvent: Event = {
            id: `new-${Date.now()}`,
            title: 'New Event',
            start: start,
            end: end,
            color: '#e3ded3'
        };
        setEvents(prev => [...prev, newEvent]);

        // Reset
        activeCreationRef.current = null;
        if (e.currentTarget.hasPointerCapture(e.pointerId)) {
            (e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId);
        }
    };

    return (
        <div className="schedule-container custom-scrollbar">
            <div className="schedule-wrapper">
                {isNewDraft && (
                    <NewDraftOverlay
                        onImportClick={onImportClick || (() => { })}
                        onStartClick={onStartClick || (() => { })}
                    />
                )}
                <div className="days-header">
                    <div className="time-spacer">
                        <div className="spacer-label spacer-day">DAY</div>
                        <div className="spacer-label spacer-date">DATE</div>
                        <div className="spacer-label spacer-port">PORT</div>
                        <div className="spacer-label spacer-empty"></div>
                    </div>
                    <div
                        className="days-grid"
                        style={{ gridTemplateColumns: `repeat(${days.length}, ${COLUMN_WIDTH_DEF})` }}
                    >
                        {days.map((day, i) => (
                            <DayHeaderCell
                                key={i}
                                day={day}
                                info={itinerary[i]}
                                index={i}
                                onDateChange={onDateChange}
                                onLocationChange={onLocationChange}
                                onTimeChange={onTimeChange}

                            />
                        ))}
                    </div>
                    <div className="time-spacer-right">
                        <div className="spacer-label spacer-day">DAY</div>
                        <div className="spacer-label spacer-date">DATE</div>
                        <div className="spacer-label spacer-port">PORT</div>
                        <div className="spacer-label spacer-empty"></div>
                    </div>
                </div>

                <div className="grid-body">
                    <div
                        className="grid-content"
                        style={{ height: `${HOURS_COUNT * PIXELS_PER_HOUR}px` }}
                    >
                        <div className="time-column">
                            <TimeColumn />
                        </div>

                        <div
                            className="events-grid"
                            style={{ gridTemplateColumns: `repeat(${days.length}, ${COLUMN_WIDTH_DEF})` }}
                            onMouseLeave={() => setHoverDay(null)} // Clear highlight on leave
                        >
                            <div className="grid-lines">
                                {Array.from({ length: HOURS_COUNT }).map((_, i) => (
                                    <div key={i} className="grid-line-hour">
                                        {Array.from({ length: 11 }).map((_, j) => {
                                            const minutes = (j + 1) * 5;
                                            const top = (minutes / 60) * PIXELS_PER_HOUR - 1;
                                            const is15Min = minutes % 15 === 0;
                                            return (
                                                <div
                                                    key={j}
                                                    className={is15Min ? "grid-line-15" : "grid-line-5"}
                                                    style={{ top: `${top}px` }}
                                                ></div>
                                            );
                                        })}
                                    </div>
                                ))}
                            </div>

                            <DndContext
                                sensors={sensors}
                                onDragStart={handleDragStart}
                                onDragMove={handleDragMove}
                                onDragEnd={handleDragEnd}
                            >
                                {days.map((day) => {
                                    const dayIso = day.toISOString();

                                    // Calculate props for this day
                                    const isHovered = hoverDay === dayIso;

                                    return (
                                        <DayColumn
                                            key={dayIso}
                                            date={day}
                                            id={dayIso}
                                            isHovered={isHovered}
                                            onClick={() => {
                                                if (isInteractionActive()) return;
                                                // Optional: Clear selection or something
                                            }}
                                            onPointerDown={(e) => handlePointerDown(e, day)}
                                            // Pointer events for hover tracking
                                            onPointerMove={(e) => handlePointerMove(e, day)}
                                            onPointerUp={handlePointerUp}
                                            highlightRef={(el) => {
                                                if (el) highlightRefs.current.set(dayIso, el);
                                                else highlightRefs.current.delete(dayIso);
                                            }}
                                            ghostRef={(el) => {
                                                if (el) ghostRefs.current.set(dayIso, el);
                                                else ghostRefs.current.delete(dayIso);
                                            }}
                                            onContextMenu={(e: React.MouseEvent) => {
                                                const rect = e.currentTarget.getBoundingClientRect();
                                                const relativeY = e.clientY - rect.top;
                                                const hour = START_HOUR + (relativeY / PIXELS_PER_HOUR);
                                                // Snap to 5 mins
                                                const snappedHour = Math.floor(hour) + Math.round((hour % 1) * 60 / SNAP_MINUTES) * SNAP_MINUTES / 60;

                                                handleContextMenu(e, 'grid', { date: day, time: snappedHour });
                                            }}
                                        >
                                            {(eventsByDay[dayIso] || []).map(({ event, style, isLate }) => (
                                                <EventBlock
                                                    key={event.id}
                                                    event={event}
                                                    style={style}
                                                    isLate={isLate}
                                                    onUpdate={handleUpdateEvent}
                                                    onDelete={handleDeleteEvent}
                                                    onContextMenu={(e, id) => {
                                                        handleContextMenu(e, 'event', id);
                                                    }}
                                                    isCopyDrag={copyDragState.isCopyDrag && copyDragState.activeDragId === event.id}
                                                />
                                            ))}
                                        </DayColumn>
                                    );
                                })}

                                {/* Ghost overlay for copy-drag mode */}
                                <DragOverlay dropAnimation={null}>
                                    {copyDragState.isCopyDrag && copyDragState.activeEvent && (
                                        <GhostEventOverlay
                                            event={copyDragState.activeEvent}
                                            dragDelta={copyDragState.delta}
                                            width={copyDragState.eventWidth}
                                            height={copyDragState.eventHeight}
                                        />
                                    )}
                                </DragOverlay>
                            </DndContext>
                        </div>

                        <div className="time-column-right">
                            <TimeColumn />
                        </div>
                    </div>

                    {/* Other Venue Shows Section */}
                    {otherVenueShows.length > 0 && (
                        <div className="other-venues-section">
                            {otherVenueShows.map((venueData, vIndex) => (
                                <div key={vIndex} className="venue-row">
                                    {/* Venue Name Label (Left) */}
                                    <div className="venue-label left">
                                        {venueData.venue}
                                    </div>

                                    {/* Days Grid */}
                                    <div className="venue-days-grid" style={{ display: 'grid', gridTemplateColumns: `repeat(${days.length}, ${COLUMN_WIDTH_DEF})` }}>
                                        {days.map((day, dIndex) => {
                                            const dateStr = format(day, 'yyyy-MM-dd');
                                            const show = venueData.shows.find(s => s.date === dateStr);

                                            return (
                                                <FooterHighlightCell
                                                    key={dIndex}
                                                    venue={venueData.venue}
                                                    date={day}
                                                    show={show}
                                                    onUpdate={onOtherVenueShowUpdate || (() => { })}
                                                />
                                            );
                                        })}
                                    </div>

                                    {/* Venue Name Label (Right) */}
                                    <div className="venue-label right">
                                        {venueData.venue}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
            <ContextMenu
                position={contextMenu?.position || null}
                items={contextMenuItems}
                onClose={handleCloseContextMenu}
            />
        </div>
    );
};
