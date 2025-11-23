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

    // Snap all transforms to 15-minute increments (25px = 15 minutes at 100px/hour)
    const SNAP_PIXELS = 25;
    const snappedTransformY = transform ? Math.round(transform.y / SNAP_PIXELS) * SNAP_PIXELS : 0;
    const snappedResizeTransformY = resizeTransform ? Math.round(resizeTransform.y / SNAP_PIXELS) * SNAP_PIXELS : 0;
    const snappedResizeTopTransformY = resizeTopTransform ? Math.round(resizeTopTransform.y / SNAP_PIXELS) * SNAP_PIXELS : 0;

    // Visual feedback for resizing (preview height change with snapping)
    const currentHeight = isResizingBottom
        ? Math.max(20, height + snappedResizeTransformY)
        : isResizingTop
            ? Math.max(20, height - snappedResizeTopTransformY)
            : height;

    const currentTop = isResizingTop
        ? top + snappedResizeTopTransformY
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
        const pixelsToMinutes = (px: number) => px * (60 / 100);

        if (isDragging && transform) {
            // Moving the entire event
            const minutesShift = pixelsToMinutes(snappedTransformY);
            const previewStart = new Date(event.start.getTime() + minutesShift * 60 * 1000);
            const previewEnd = new Date(event.end.getTime() + minutesShift * 60 * 1000);
            return { start: previewStart, end: previewEnd };
        } else if (isResizingTop && resizeTopTransform) {
            // Resizing from top
            const minutesShift = pixelsToMinutes(snappedResizeTopTransformY);
            const previewStart = new Date(event.start.getTime() + minutesShift * 60 * 1000);
            return { start: previewStart, end: event.end };
        } else if (isResizingBottom && resizeTransform) {
            // Resizing from bottom
            const minutesShift = pixelsToMinutes(snappedResizeTransformY);
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
                isDragging && "dragging",
                (isResizingBottom || isResizingTop) && "resizing"
            )}
        >
            <div className="event-content">
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
