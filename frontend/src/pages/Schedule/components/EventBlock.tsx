import React from 'react';
import { useDraggable } from '@dnd-kit/core';
import clsx from 'clsx';
import { format } from 'date-fns';
import { Edit2, Trash2, MoreHorizontal } from 'lucide-react';
import type { Event } from '../../../types';
import { getContrastColor } from '../../../utils/eventColors';
import { ColorSelector } from './ColorSelector';

interface EventBlockProps {
    event: Event;
    style: React.CSSProperties;
    isLate?: boolean;
    onUpdate?: (eventId: string, updates: { title?: string; timeDisplay?: string; color?: string }) => void;
    onDelete?: (eventId: string) => void;
    onContextMenu?: (e: React.MouseEvent, eventId: string) => void;
}

const PIXELS_PER_HOUR = 100;
const SNAP_MINUTES = 5;
const MIN_HEIGHT = 25; // Minimum 15 minutes

const EventBlockComponent: React.FC<EventBlockProps> = ({ event, style: containerStyle, isLate, onUpdate, onDelete, onContextMenu }) => {
    const defaultTimeLabel = `${format(event.start, 'h:mm a')} - ${isLate ? 'Late' : format(event.end, 'h:mm a')}`;

    // Separate edit states
    const [isEditingTitle, setIsEditingTitle] = React.useState(false);
    const [isEditingTime, setIsEditingTime] = React.useState(false);

    // Color Selector state
    const [isColorSelectorOpen, setIsColorSelectorOpen] = React.useState(false);
    const colorTriggerRef = React.useRef<HTMLDivElement>(null);

    const [editTitle, setEditTitle] = React.useState(event.title);
    const [editTimeDisplay, setEditTimeDisplay] = React.useState(event.timeDisplay || defaultTimeLabel);

    const timeoutRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);
    const lastTimeClickRef = React.useRef(0);
    const lastTitleClickRef = React.useRef(0);
    const titleInputRef = React.useRef<HTMLInputElement>(null);
    const timeInputRef = React.useRef<HTMLInputElement>(null);
    const domRef = React.useRef<HTMLDivElement | null>(null);



    // Reset state when event changes
    React.useEffect(() => {
        setEditTitle(event.title);
        setEditTimeDisplay(event.timeDisplay || defaultTimeLabel);
    }, [event.title, event.timeDisplay, defaultTimeLabel]);

    React.useEffect(() => {
        return () => {
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
            }
        };
    }, []);

    const handleSaveTitle = () => {
        if (Date.now() - lastTitleClickRef.current < 200) return;
        timeoutRef.current = setTimeout(() => {
            if (onUpdate && editTitle !== event.title) {
                onUpdate(event.id, { title: editTitle });
            }
            setIsEditingTitle(false);
        }, 50);
    };

    const handleSaveTime = () => {
        if (Date.now() - lastTimeClickRef.current < 200) return;
        const newTime = editTimeDisplay.trim();
        const currentTime = event.timeDisplay || defaultTimeLabel;
        if (newTime !== currentTime) {
            timeoutRef.current = setTimeout(() => {
                if (onUpdate) {
                    onUpdate(event.id, { timeDisplay: newTime || undefined });
                }
                setIsEditingTime(false);
            }, 50);
        } else {
            setIsEditingTime(false);
        }
    };

    const handleKeyDownTitle = (e: React.KeyboardEvent) => {
        e.stopPropagation();
        if (e.key === 'Enter') {
            (e.currentTarget as HTMLInputElement).blur();
        } else if (e.key === 'Escape') {
            setEditTitle(event.title);
            setIsEditingTitle(false);
        }
    };

    const handleKeyDownTime = (e: React.KeyboardEvent) => {
        e.stopPropagation();
        if (e.key === 'Enter') {
            (e.currentTarget as HTMLInputElement).blur();
        } else if (e.key === 'Escape') {
            setEditTimeDisplay(event.timeDisplay || defaultTimeLabel);
            setIsEditingTime(false);
        }
    };

    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
        id: event.id,
        data: { type: 'event', event },
        disabled: isEditingTitle || isEditingTime || isColorSelectorOpen
    });

    const setRefs = React.useCallback((node: HTMLDivElement | null) => {
        setNodeRef(node);
        domRef.current = node;
    }, [setNodeRef]);

    const {
        attributes: resizeAttrs,
        listeners: resizeListeners,
        setNodeRef: setResizeRef,
        transform: resizeTransform,
        isDragging: isResizingBottom
    } = useDraggable({
        id: `${event.id}-resize-bottom`,
        data: { type: 'resize-bottom', event },
        disabled: isEditingTitle || isEditingTime || isColorSelectorOpen
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
        disabled: isEditingTitle || isEditingTime || isColorSelectorOpen
    });

    const height = parseFloat(containerStyle.height as string) || 60;
    const top = parseFloat(containerStyle.top as string) || 0;
    const SNAP_PIXELS = PIXELS_PER_HOUR / (60 / SNAP_MINUTES);
    const snappedTransformY = transform ? Math.round(transform.y / SNAP_PIXELS) * SNAP_PIXELS : 0;
    const snappedResizeTransformY = resizeTransform ? Math.round(resizeTransform.y / SNAP_PIXELS) * SNAP_PIXELS : 0;
    const snappedResizeTopTransformY = resizeTopTransform ? Math.round(resizeTopTransform.y / SNAP_PIXELS) * SNAP_PIXELS : 0;
    const currentHeight = isResizingBottom
        ? Math.max(MIN_HEIGHT, height + snappedResizeTransformY)
        : isResizingTop
            ? Math.max(MIN_HEIGHT, height - snappedResizeTopTransformY)
            : height;
    const currentTop = isResizingTop ? top + (height - currentHeight) : top;
    const visualTop = isDragging && transform ? top + snappedTransformY : currentTop;

    const positionStyle: React.CSSProperties = {
        top: `${visualTop}px`,
        height: `${currentHeight}px`,
        left: containerStyle.left,
        width: containerStyle.width,
        zIndex: isDragging || isResizingBottom || isResizingTop || isEditingTitle || isEditingTime || isColorSelectorOpen ? 80 : 10,
        transform: (isDragging && transform) ? `translate3d(${transform.x}px, 0, 0)` : undefined,
        paddingRight: '1px',
        paddingBottom: '2px',
        boxSizing: 'border-box'
    };

    const visualStyle: React.CSSProperties = {
        background: event.color,
        color: getContrastColor(event.color),
        overflow: (!isEditingTitle && !isEditingTime) ? 'hidden' : 'visible'
    };


    const isSmallDuration = currentHeight < 50;

    const getPreviewTimes = () => {
        const pixelsToMinutes = (px: number) => {
            const minutes = px * (60 / PIXELS_PER_HOUR);
            return Math.round(minutes / SNAP_MINUTES) * SNAP_MINUTES;
        };
        if (isDragging && transform) {
            const minutesShift = pixelsToMinutes(snappedTransformY);
            const previewStart = new Date(event.start.getTime() + minutesShift * 60 * 1000);
            const previewEnd = new Date(event.end.getTime() + minutesShift * 60 * 1000);
            return { start: previewStart, end: previewEnd };
        } else if (isResizingTop) {
            let minutesShift = pixelsToMinutes(snappedResizeTopTransformY);
            const currentDurationMinutes = (event.end.getTime() - event.start.getTime()) / (1000 * 60);
            if (currentDurationMinutes - minutesShift < 15) minutesShift = currentDurationMinutes - 15;
            const previewStart = new Date(event.start.getTime() + minutesShift * 60 * 1000);
            return { start: previewStart, end: event.end };
        } else if (isResizingBottom) {
            let minutesShift = pixelsToMinutes(snappedResizeTransformY);
            const currentDurationMinutes = (event.end.getTime() - event.start.getTime()) / (1000 * 60);
            if (currentDurationMinutes + minutesShift < 15) minutesShift = 15 - currentDurationMinutes;
            const previewEnd = new Date(event.end.getTime() + minutesShift * 60 * 1000);
            return { start: event.start, end: previewEnd };
        }
        return { start: event.start, end: event.end };
    };

    const { start: displayStart, end: displayEnd } = getPreviewTimes();
    const timeLabel = (isDragging || isResizingBottom || isResizingTop)
        ? `${format(displayStart, 'h:mm a')} - ${isLate ? 'Late' : format(displayEnd, 'h:mm a')}`
        : (event.timeDisplay || `${format(displayStart, 'h:mm a')} - ${isLate ? 'Late' : format(displayEnd, 'h:mm a')}`);
    const isInteracting = isDragging || isResizingBottom || isResizingTop;

    React.useEffect(() => {
        const node = domRef.current;
        if (!node || !onContextMenu) return;

        const handleContextMenu = (e: MouseEvent) => {
            e.preventDefault();
            e.stopPropagation();
            onContextMenu(e as unknown as React.MouseEvent, event.id);
        };

        node.addEventListener('contextmenu', handleContextMenu);
        return () => {
            node.removeEventListener('contextmenu', handleContextMenu);
        }
    }, [event.id, onContextMenu]);

    return (
        <div
            ref={setRefs}
            style={positionStyle}
            {...listeners}
            {...attributes}
            className={clsx(
                "event-block",
                isDragging && "dragging",
                (isResizingBottom || isResizingTop) && "resizing",
                "group",
                isSmallDuration && "is-compact"
            )}

        >
            <div
                className={clsx(
                    "event-box w-full h-full relative rounded",
                    (!isEditingTitle && !isEditingTime) ? "overflow-hidden" : "overflow-visible"
                )}
                style={visualStyle}
            >
                {/* Color Indicator / Selector Trigger */}
                {!isEditingTitle && !isEditingTime && (
                    <div
                        ref={colorTriggerRef}
                        className={clsx("event-control-trigger type-trigger", isColorSelectorOpen && "force-visible")}
                        onPointerDown={(e) => {
                            e.stopPropagation(); // Prevent drag start
                            setIsColorSelectorOpen(true);
                        }}
                        title={`Change Color`}
                    >
                        <MoreHorizontal size={16} strokeWidth={2} />
                    </div>
                )}

                {/* Color Selector Portal */}
                <ColorSelector
                    isOpen={isColorSelectorOpen}
                    onClose={() => setIsColorSelectorOpen(false)}
                    triggerRef={colorTriggerRef}
                    currentColor={event.color}
                    onSelect={(color) => {
                        if (onUpdate) {
                            onUpdate(event.id, { color });
                        }
                    }}
                />

                {/* Delete Button (Top Right) */}
                {
                    !isEditingTitle && !isEditingTime && onDelete && (
                        <button
                            className="delete-event-btn"
                            onPointerDown={(e) => {
                                e.stopPropagation();
                                onDelete(event.id);
                            }}
                            title="Delete Event"
                        >
                            <Trash2 size={13} strokeWidth={2.5} />
                        </button>
                    )
                }


                {/* Top Handle */}
                {
                    !isEditingTitle && !isEditingTime && (
                        <div
                            ref={setResizeTopRef}
                            {...resizeTopListeners}
                            {...resizeTopAttrs}
                            className="resize-handle resize-handle-top"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <div className="resize-bar"></div>
                        </div>
                    )
                }

                <div className="event-content" style={{ position: 'relative', height: '100%' }}>
                    {/* Full View */}
                    <div className="event-content-full">
                        {/* Time Section */}
                        <div
                            className="event-time flex justify-center items-center relative select-none cursor-pointer"
                            style={{ minHeight: '1.2em' }}
                            onPointerDown={(e) => {
                                const now = Date.now();
                                if (now - lastTimeClickRef.current < 300) {
                                    e.stopPropagation();
                                    if (timeoutRef.current) clearTimeout(timeoutRef.current);
                                    setEditTimeDisplay(event.timeDisplay || defaultTimeLabel);
                                    setIsEditingTime(true);
                                }
                                lastTimeClickRef.current = now;
                            }}
                        >
                            <div className={`relative inline-block group-time-wrapper ${isEditingTime ? 'invisible' : ''}`} style={{ visibility: isEditingTime ? 'hidden' : 'visible' }}>
                                <span>{timeLabel}</span>
                                {!isInteracting && (
                                    <span className="pencil-spacer">
                                        <span role="button" className="edit-icon-btn" onPointerDown={(e) => e.stopPropagation()} onClick={(e) => { e.stopPropagation(); setIsEditingTime(true); }} > <Edit2 size={10} className="edit-icon-svg" /> </span>
                                    </span>
                                )}
                            </div>
                            {isEditingTime && !isSmallDuration && (
                                <div className="absolute inset-0 flex items-center justify-center z-50">
                                    <input
                                        ref={(el) => { timeInputRef.current = el; if (el) setTimeout(() => el.focus(), 0); }}
                                        type="text" value={editTimeDisplay} onChange={(e) => setEditTimeDisplay(e.target.value)} onBlur={handleSaveTime} onKeyDown={handleKeyDownTime} onFocus={(e) => e.target.setSelectionRange(e.target.value.length, e.target.value.length)} onPointerDown={(e) => e.stopPropagation()} className="glass-input-event"
                                        style={{ '--event-color': event.color, width: `calc(${editTimeDisplay.length}ch + 3rem)`, minWidth: '100%' } as React.CSSProperties}
                                    />
                                </div>
                            )}
                        </div>

                        {/* Title Section */}
                        <div
                            className="event-title flex justify-center items-center relative select-none cursor-pointer"
                            style={{ minHeight: '1.2em' }}
                            onPointerDown={(e) => {
                                const now = Date.now();
                                if (now - lastTitleClickRef.current < 300) {
                                    e.stopPropagation();
                                    if (timeoutRef.current) clearTimeout(timeoutRef.current);
                                    setIsEditingTitle(true);
                                }
                                lastTitleClickRef.current = now;
                            }}
                        >
                            <div className={`relative inline-block group-title-wrapper ${isEditingTitle ? 'invisible' : ''}`} style={{ visibility: isEditingTitle ? 'hidden' : 'visible' }}>
                                <span>{event.title}</span>
                                {!isInteracting && (
                                    <span className="pencil-spacer">
                                        <span role="button" className="edit-icon-btn" onPointerDown={(e) => e.stopPropagation()} onClick={(e) => { e.stopPropagation(); setIsEditingTitle(true); }} > <Edit2 size={10} className="edit-icon-svg" /> </span>
                                    </span>
                                )}
                            </div>
                            {isEditingTitle && !isSmallDuration && (
                                <div className="absolute inset-0 flex items-center justify-center z-50">
                                    <input
                                        ref={(el) => { titleInputRef.current = el; if (el) setTimeout(() => el.focus(), 0); }}
                                        type="text" value={editTitle} onChange={(e) => setEditTitle(e.target.value)} onBlur={handleSaveTitle} onKeyDown={handleKeyDownTitle} onFocus={(e) => e.target.setSelectionRange(e.target.value.length, e.target.value.length)} onPointerDown={(e) => e.stopPropagation()} className="glass-input-event"
                                        style={{ '--event-color': event.color, width: `calc(${editTitle.length}ch + 3rem)`, minWidth: '100%' } as React.CSSProperties}
                                    />
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Compact View */}
                    {isSmallDuration && (
                        <div className="event-content-compact group/compact select-none cursor-pointer relative" style={{ overflow: 'visible', display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', width: '100%', padding: 0, margin: 0, gap: '0.25rem' }}>
                            {!isEditingTime && !isEditingTitle && (
                                <>
                                    <span className="event-time-compact hover:text-blue-600 transition-colors relative" onPointerDown={(e) => { const now = Date.now(); if (now - lastTimeClickRef.current < 300) { e.stopPropagation(); if (timeoutRef.current) clearTimeout(timeoutRef.current); setEditTimeDisplay(event.timeDisplay || defaultTimeLabel); setIsEditingTime(true); } lastTimeClickRef.current = now; }}>{timeLabel.split('-')[0]}</span>
                                    <span>-</span>
                                    <span className="truncate hover:text-blue-600 transition-colors relative" onPointerDown={(e) => { const now = Date.now(); if (now - lastTitleClickRef.current < 300) { e.stopPropagation(); if (timeoutRef.current) clearTimeout(timeoutRef.current); setIsEditingTitle(true); } lastTitleClickRef.current = now; }}><span>{event.title}</span></span>
                                </>
                            )}
                            {(isEditingTime || isEditingTitle) && (
                                <div className="absolute inset-0 z-50" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', width: '100%' }}>
                                    {isEditingTime ? (
                                        <input ref={(el) => { timeInputRef.current = el; if (el) setTimeout(() => el.focus(), 0); }} type="text" value={editTimeDisplay} onChange={(e) => setEditTimeDisplay(e.target.value)} onBlur={handleSaveTime} onKeyDown={handleKeyDownTime} onFocus={(e) => e.target.setSelectionRange(e.target.value.length, e.target.value.length)} onPointerDown={(e) => e.stopPropagation()} className="glass-input-event text-center font-medium" style={{ '--event-color': event.color, width: '100%', height: '100%', fontSize: 'inherit', padding: '0', margin: '0', color: getContrastColor(event.color) } as React.CSSProperties} />
                                    ) : (
                                        <input ref={(el) => { titleInputRef.current = el; if (el) setTimeout(() => el.focus(), 0); }} type="text" value={editTitle} onChange={(e) => setEditTitle(e.target.value)} onBlur={handleSaveTitle} onKeyDown={handleKeyDownTitle} onFocus={(e) => e.target.setSelectionRange(e.target.value.length, e.target.value.length)} onPointerDown={(e) => e.stopPropagation()} className="glass-input-event text-center font-medium" style={{ '--event-color': event.color, width: '100%', height: '100%', fontSize: 'inherit', padding: '0', margin: '0', color: getContrastColor(event.color) } as React.CSSProperties} />
                                    )}
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Bottom Handle */}
                {
                    !isEditingTitle && !isEditingTime && (
                        <div ref={setResizeRef} {...resizeListeners} {...resizeAttrs} className="resize-handle" onClick={(e) => e.stopPropagation()}>
                            <div className="resize-bar"></div>
                        </div>
                    )
                }
            </div >
        </div>
    );
};

export const EventBlock = React.memo(EventBlockComponent);
