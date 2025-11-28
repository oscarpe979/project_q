import React from 'react';
import { useDraggable } from '@dnd-kit/core';
import clsx from 'clsx';
import { format } from 'date-fns';
import { Edit2 } from 'lucide-react';
import type { Event } from '../../types';
import { getContrastColor } from '../../utils/eventColors';

interface EventBlockProps {
    event: Event;
    style: React.CSSProperties;
    isLate?: boolean;
    onUpdate?: (eventId: string, updates: { title?: string; timeDisplay?: string }) => void;
}

const PIXELS_PER_HOUR = 100;
const SNAP_MINUTES = 5;
const MIN_HEIGHT = 25; // Minimum 15 minutes

export const EventBlock: React.FC<EventBlockProps> = ({ event, style: containerStyle, isLate, onUpdate }) => {
    const defaultTimeLabel = `${format(event.start, 'h:mm a')} - ${isLate ? 'Late' : format(event.end, 'h:mm a')}`;

    // Separate edit states
    const [isEditingTitle, setIsEditingTitle] = React.useState(false);
    const [isEditingTime, setIsEditingTime] = React.useState(false);

    const [editTitle, setEditTitle] = React.useState(event.title);
    const [editTimeDisplay, setEditTimeDisplay] = React.useState(event.timeDisplay || defaultTimeLabel);

    // Reset state when event changes
    React.useEffect(() => {
        setEditTitle(event.title);
        setEditTimeDisplay(event.timeDisplay || defaultTimeLabel);
    }, [event.title, event.timeDisplay, defaultTimeLabel]);

    const handleSaveTitle = () => {
        if (onUpdate && editTitle !== event.title) {
            onUpdate(event.id, { title: editTitle });
        }
        setIsEditingTitle(false);
    };

    const handleSaveTime = () => {
        const newTime = editTimeDisplay.trim();
        if (onUpdate) {
            onUpdate(event.id, { timeDisplay: newTime || undefined });
        }
        setIsEditingTime(false);
    };

    const handleKeyDownTitle = (e: React.KeyboardEvent) => {
        e.stopPropagation();
        if (e.key === 'Enter') {
            handleSaveTitle();
        } else if (e.key === 'Escape') {
            setEditTitle(event.title);
            setIsEditingTitle(false);
        }
    };

    const handleKeyDownTime = (e: React.KeyboardEvent) => {
        e.stopPropagation();
        if (e.key === 'Enter') {
            handleSaveTime();
        } else if (e.key === 'Escape') {
            setEditTimeDisplay(event.timeDisplay || defaultTimeLabel);
            setIsEditingTime(false);
        }
    };

    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
        id: event.id,
        data: { type: 'event', event },
        disabled: isEditingTitle || isEditingTime
    });

    const {
        attributes: resizeAttrs,
        listeners: resizeListeners,
        setNodeRef: setResizeRef,
        transform: resizeTransform,
        isDragging: isResizingBottom
    } = useDraggable({
        id: `${event.id}-resize-bottom`,
        data: { type: 'resize-bottom', event },
        disabled: isEditingTitle || isEditingTime
    });

    const {
        attributes: resizeTopAttrs,
        listeners: resizeTopListeners,
        setNodeRef: setResizeTopRef,
        transform: resizeTopTransform,
        isDragging: isResizingTop
    } = useDraggable({
        id: `${event.id}-resize-top`,
        data: { type: 'resize-top', event },
        disabled: isEditingTitle || isEditingTime
    });

    const height = parseFloat(containerStyle.height as string) || 60;
    const top = parseFloat(containerStyle.top as string) || 0;

    // Snap calculations
    const SNAP_PIXELS = PIXELS_PER_HOUR / (60 / SNAP_MINUTES);
    const snappedTransformY = transform ? Math.round(transform.y / SNAP_PIXELS) * SNAP_PIXELS : 0;
    const snappedResizeTransformY = resizeTransform ? Math.round(resizeTransform.y / SNAP_PIXELS) * SNAP_PIXELS : 0;
    const snappedResizeTopTransformY = resizeTopTransform ? Math.round(resizeTopTransform.y / SNAP_PIXELS) * SNAP_PIXELS : 0;

    // Visual feedback for resizing (preview height change with snapping)
    const currentHeight = isResizingBottom
        ? Math.max(MIN_HEIGHT, height + snappedResizeTransformY)
        : isResizingTop
            ? Math.max(MIN_HEIGHT, height - snappedResizeTopTransformY)
            : height;

    const currentTop = isResizingTop
        ? top + (height - currentHeight)
        : top;

    // Calculate visual top position during drag
    const visualTop = isDragging && transform
        ? top + snappedTransformY
        : currentTop;

    const style: React.CSSProperties = {
        top: `${visualTop}px`,
        height: `${currentHeight}px`,
        left: containerStyle.left,
        width: containerStyle.width,
        zIndex: isDragging || isResizingBottom || isResizingTop || isEditingTitle || isEditingTime ? 50 : 10,
        transform: (isDragging && transform) ? `translate3d(${transform.x}px, 0, 0)` : undefined,
        background: event.color,
        color: getContrastColor(event.color),
        border: '2px solid rgba(0, 0, 0, 0.14)'
    };

    // Dynamic styles based on event type
    const getEventClass = () => {
        switch (event.type) {
            case 'show': return "event-show";
            case 'rehearsal': return "event-rehearsal";
            case 'maintenance': return "event-maintenance";
            default: return "event-other";
        }
    };

    const isSmallDuration = currentHeight < 50;

    // Calculate preview times during drag/resize
    const getPreviewTimes = () => {
        // Calculate duration in minutes based on the CLAMPED visual height
        const durationMinutes = Math.round((currentHeight / PIXELS_PER_HOUR) * 60);

        if (isDragging && transform) {
            // Moving the entire event
            const pixelsToMinutes = (px: number) => {
                const minutes = px * (60 / PIXELS_PER_HOUR);
                return Math.round(minutes / SNAP_MINUTES) * SNAP_MINUTES;
            };
            const minutesShift = pixelsToMinutes(snappedTransformY);
            const previewStart = new Date(event.start.getTime() + minutesShift * 60 * 1000);
            const previewEnd = new Date(event.end.getTime() + minutesShift * 60 * 1000);
            return { start: previewStart, end: previewEnd };
        } else if (isResizingTop) {
            // Resizing from top: End is fixed, Start is derived from duration
            const previewStart = new Date(event.end.getTime() - durationMinutes * 60 * 1000);
            return { start: previewStart, end: event.end };
        } else if (isResizingBottom) {
            // Resizing from bottom: Start is fixed, End is derived from duration
            const previewEnd = new Date(event.start.getTime() + durationMinutes * 60 * 1000);
            return { start: event.start, end: previewEnd };
        }
        return { start: event.start, end: event.end };
    };

    const { start: displayStart, end: displayEnd } = getPreviewTimes();

    const timeLabel = (isDragging || isResizingBottom || isResizingTop)
        ? `${format(displayStart, 'h:mm a')} - ${isLate ? 'Late' : format(displayEnd, 'h:mm a')}`
        : (event.timeDisplay || `${format(displayStart, 'h:mm a')} - ${isLate ? 'Late' : format(displayEnd, 'h:mm a')}`);

    const isInteracting = isDragging || isResizingBottom || isResizingTop;

    return (
        <div
            ref={setNodeRef}
            style={style}
            {...listeners}
            {...attributes}
            className={clsx(
                "event-block",
                getEventClass(),
                isSmallDuration && "is-compact",
                isDragging && "dragging",
                (isResizingBottom || isResizingTop) && "resizing",
                "group"
            )}
        >
            {/* Top Resize Handle */}
            {!isEditingTitle && !isEditingTime && (
                <div
                    ref={setResizeTopRef}
                    {...resizeTopListeners}
                    {...resizeTopAttrs}
                    className="resize-handle resize-handle-top"
                    onClick={(e) => e.stopPropagation()}
                >
                    <div className="resize-bar"></div>
                </div>
            )}

            <div className="event-content" style={{ position: 'relative', height: '100%' }}>
                <div className="event-content-full">

                    {/* Time Section */}
                    <div className="event-time flex justify-center" style={{ minHeight: '1.2em' }}>
                        {isEditingTime ? (
                            <input
                                type="text"
                                value={editTimeDisplay}
                                onChange={(e) => setEditTimeDisplay(e.target.value)}
                                onBlur={handleSaveTime}
                                onKeyDown={handleKeyDownTime}
                                autoFocus
                                onPointerDown={(e) => e.stopPropagation()}
                                className="bg-transparent border-none outline-none p-0 w-full"
                                style={{
                                    fontFamily: 'inherit',
                                    fontSize: 'inherit',
                                    color: 'inherit',
                                    background: 'transparent',
                                    border: 'none',
                                    borderBottom: '1px solid currentColor',
                                    outline: 'none',
                                    boxShadow: 'none',
                                    textAlign: 'center',
                                    opacity: 0.9
                                }}
                            />
                        ) : (
                            <div className="relative flex items-center group-time-wrapper">
                                <span>{timeLabel}</span>
                                {!isInteracting && (
                                    <button
                                        className="edit-icon-btn"
                                        onPointerDown={(e) => e.stopPropagation()}
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            setIsEditingTime(true);
                                        }}
                                        style={{
                                            position: 'absolute',
                                            left: '100%',
                                            marginLeft: '4px',
                                            background: 'transparent',
                                            border: 'none',
                                            cursor: 'pointer',
                                            padding: 0,
                                            display: 'flex',
                                            alignItems: 'center',
                                            opacity: 0,
                                            color: 'inherit'
                                        }}
                                    >
                                        <Edit2 size={10} className="edit-icon-svg" />
                                    </button>
                                )}
                                <style>{`
                                    .group-time-wrapper:hover .edit-icon-btn {
                                        opacity: 1 !important;
                                    }
                                    .edit-icon-svg {
                                        opacity: 0.8;
                                        transition: opacity 0.2s;
                                    }
                                    .edit-icon-btn:hover .edit-icon-svg {
                                        opacity: 1;
                                    }
                                `}</style>
                            </div>
                        )}
                    </div>

                    {/* Title Section */}
                    <div className="event-title flex justify-center" style={{ minHeight: '1.2em' }}>
                        {isEditingTitle ? (
                            <input
                                type="text"
                                value={editTitle}
                                onChange={(e) => setEditTitle(e.target.value)}
                                onBlur={handleSaveTitle}
                                onKeyDown={handleKeyDownTitle}
                                autoFocus
                                onPointerDown={(e) => e.stopPropagation()}
                                className="bg-transparent border-none outline-none p-0 w-full font-bold"
                                style={{
                                    fontFamily: 'inherit',
                                    fontSize: 'inherit',
                                    color: 'inherit',
                                    background: 'transparent',
                                    border: 'none',
                                    borderBottom: '1px solid currentColor',
                                    outline: 'none',
                                    boxShadow: 'none',
                                    textAlign: 'center',
                                    opacity: 0.9
                                }}
                            />
                        ) : (
                            <div className="relative flex items-center group-title-wrapper">
                                <span>{event.title}</span>
                                {!isInteracting && (
                                    <button
                                        className="edit-icon-btn"
                                        onPointerDown={(e) => e.stopPropagation()}
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            setIsEditingTitle(true);
                                        }}
                                        style={{
                                            position: 'absolute',
                                            left: '100%',
                                            marginLeft: '4px',
                                            background: 'transparent',
                                            border: 'none',
                                            cursor: 'pointer',
                                            padding: 0,
                                            display: 'flex',
                                            alignItems: 'center',
                                            opacity: 0,
                                            color: 'inherit'
                                        }}
                                    >
                                        <Edit2 size={10} className="edit-icon-svg" />
                                    </button>
                                )}
                                <style>{`
                                    .group-title-wrapper:hover .edit-icon-btn {
                                        opacity: 1 !important;
                                    }
                                    .edit-icon-svg {
                                        opacity: 0.8;
                                        transition: opacity 0.2s;
                                    }
                                    .edit-icon-btn:hover .edit-icon-svg {
                                        opacity: 1;
                                    }
                                `}</style>
                            </div>
                        )}
                    </div>
                </div>

                {/* Compact View (1 line) - Simplified for now, maybe disable editing in compact or just show title edit */}
                <div className="event-content-compact flex items-center gap-1 group/compact">
                    <span className="event-time-compact">{timeLabel.split('-')[0]}</span> -
                    {isEditingTitle ? (
                        <input
                            type="text"
                            value={editTitle}
                            onChange={(e) => setEditTitle(e.target.value)}
                            onBlur={handleSaveTitle}
                            onKeyDown={handleKeyDownTitle}
                            autoFocus
                            onPointerDown={(e) => e.stopPropagation()}
                            className="bg-transparent border-none outline-none p-0 w-full font-bold"
                            style={{
                                fontFamily: 'inherit',
                                fontSize: 'inherit',
                                color: 'inherit',
                                background: 'rgba(255,255,255,0.2)',
                                borderRadius: '2px'
                            }}
                        />
                    ) : (
                        <>
                            <span>{event.title}</span>
                            {!isInteracting && (
                                <button
                                    className="opacity-0 group-hover/compact:opacity-100 transition-opacity duration-200 p-0.5 rounded hover:bg-black/10"
                                    onPointerDown={(e) => e.stopPropagation()}
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        setIsEditingTitle(true);
                                    }}
                                >
                                    <Edit2 size={10} className="text-current opacity-70" />
                                </button>
                            )}
                        </>
                    )}
                </div>
            </div>

            {/* Bottom Resize Handle */}
            {!isEditingTitle && !isEditingTime && (
                <div
                    ref={setResizeRef}
                    {...resizeListeners}
                    {...resizeAttrs}
                    className="resize-handle"
                    onClick={(e) => e.stopPropagation()}
                >
                    <div className="resize-bar"></div>
                </div>
            )}
        </div>
    );
};
