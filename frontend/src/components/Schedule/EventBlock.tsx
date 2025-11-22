import React from 'react';
import { useDraggable } from '@dnd-kit/core';
import clsx from 'clsx';
import { format } from 'date-fns';

export interface Event {
    id: string;
    title: string;
    start: Date;
    end: Date;
    type: 'show' | 'rehearsal' | 'maintenance' | 'other';
}

interface EventBlockProps {
    event: Event;
    style: React.CSSProperties;
}

export const EventBlock: React.FC<EventBlockProps> = ({ event, style: containerStyle }) => {
    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
        id: event.id,
        data: { type: 'event', event },
    });

    const {
        attributes: resizeAttrs,
        listeners: resizeListeners,
        setNodeRef: setResizeRef,
        transform: resizeTransform,
        isDragging: isResizing
    } = useDraggable({
        id: `${event.id}-resize`,
        data: { type: 'resize', event },
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

    // Visual feedback for resizing (preview height change)
    const currentHeight = isResizing
        ? Math.max(20, height + (resizeTransform ? resizeTransform.y : 0))
        : isResizingTop
            ? Math.max(20, height - (resizeTopTransform ? resizeTopTransform.y : 0))
            : height;

    const currentTop = isResizingTop
        ? top + (resizeTopTransform ? resizeTopTransform.y : 0)
        : top;

    // Snap transform to 15-minute increments to match final position
    const snappedTransformY = transform ? Math.round(transform.y / 15) * 15 : 0;

    // Calculate visual top position during drag
    const visualTop = isDragging && transform
        ? top + snappedTransformY
        : currentTop;

    const style: React.CSSProperties = {
        top: `${visualTop}px`,
        height: `${currentHeight}px`,
        left: containerStyle.left,
        width: containerStyle.width,
        zIndex: isDragging || isResizing || isResizingTop ? 50 : 10,
        // Only apply horizontal transform for cross-day movement
        transform: (isDragging && transform) ? `translate3d(${transform.x}px, 0, 0)` : undefined,
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

    const isSmallDuration = currentHeight < 40;

    // Calculate preview times during drag/resize
    const getPreviewTimes = () => {
        if (isDragging && transform) {
            // Moving the entire event
            const previewStart = new Date(event.start.getTime() + snappedTransformY * 60 * 1000);
            const previewEnd = new Date(event.end.getTime() + snappedTransformY * 60 * 1000);
            return { start: previewStart, end: previewEnd };
        } else if (isResizingTop && resizeTopTransform) {
            // Resizing from top
            const minutesShift = Math.round(resizeTopTransform.y / 15) * 15;
            const previewStart = new Date(event.start.getTime() + minutesShift * 60 * 1000);
            return { start: previewStart, end: event.end };
        } else if (isResizing && resizeTransform) {
            // Resizing from bottom
            const minutesShift = Math.round(resizeTransform.y / 15) * 15;
            const previewEnd = new Date(event.end.getTime() + minutesShift * 60 * 1000);
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
                (isDragging || isResizing || isResizingTop) && "dragging"
            )}
        >
            <div style={{ display: 'flex', flexDirection: 'column', height: '100%', position: 'relative' }}>
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

                <div className="event-title">
                    {event.title}
                </div>
                {!isSmallDuration && (
                    <div className="event-time">
                        {format(displayStart, 'h:mm a')} - {format(displayEnd, 'h:mm a')}
                    </div>
                )}

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
        </div>
    );
};
