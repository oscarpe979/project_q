import React from 'react';
import { useDraggable } from '@dnd-kit/core';
import clsx from 'clsx';
import { format } from 'date-fns';
import type { Event } from '../../types';
import { getContrastColor } from '../../utils/eventColors';

interface EventBlockProps {
    event: Event;
    style: React.CSSProperties;
    isLate?: boolean;
}

const PIXELS_PER_HOUR = 100;
const SNAP_MINUTES = 5;
const MIN_HEIGHT = 25; // Minimum 15 minutes

export const EventBlock: React.FC<EventBlockProps> = ({ event, style: containerStyle, isLate }) => {
    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
        id: event.id,
        data: { type: 'event', event },
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
        zIndex: isDragging || isResizingBottom || isResizingTop ? 50 : 10,
        transform: (isDragging && transform) ? `translate3d(${transform.x}px, 0, 0)` : undefined,
        background: event.color,
        color: getContrastColor(event.color),
        borderLeft: event.color ? `4px solid ${event.color}` : undefined,
        borderColor: event.color ? 'transparent' : undefined
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
                (isResizingBottom || isResizingTop) && "resizing"
            )}
        >
            {/* Top Resize Handle */}
            <div
                ref={setResizeTopRef}
                {...resizeTopListeners}
                {...resizeTopAttrs}
                className="resize-handle resize-handle-top"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="resize-bar"></div>
            </div>

            <div className="event-content">
                {/* Full View (2 lines) */}
                <div className="event-content-full">
                    <div className="event-time">
                        {format(displayStart, 'h:mm a')} - {isLate ? 'Late' : format(displayEnd, 'h:mm a')}
                    </div>
                    <div className="event-title">
                        {event.title}
                    </div>
                </div>

                {/* Compact View (1 line) */}
                <div className="event-content-compact">
                    <span className="event-time-compact">{format(displayStart, 'h:mm a')}</span> - {event.title}
                </div>
            </div>

            {/* Bottom Resize Handle */}
            <div
                ref={setResizeRef}
                {...resizeListeners}
                {...resizeAttrs}
                className="resize-handle"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="resize-bar"></div>
            </div>
        </div>
    );
};
