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

    const height = parseFloat(containerStyle.height as string) || 60;
    const top = parseFloat(containerStyle.top as string) || 0;

    // Visual feedback for resizing (preview height change)
    const currentHeight = isResizing
        ? Math.max(20, height + (resizeTransform ? resizeTransform.y : 0))
        : height;

    const style: React.CSSProperties = {
        top: `${top}px`,
        height: `${currentHeight}px`,
        left: containerStyle.left,
        width: containerStyle.width,
        transform: transform ? `translate3d(${transform.x}px, ${transform.y}px, 0)` : undefined,
        zIndex: isDragging || isResizing ? 50 : 10,
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

    return (
        <div
            ref={setNodeRef}
            style={style}
            {...listeners}
            {...attributes}
            className={clsx(
                "event-block",
                getEventClass(),
                (isDragging || isResizing) && "dragging"
            )}
        >
            <div style={{ display: 'flex', flexDirection: 'column', height: '100%', position: 'relative' }}>
                <div className="event-title">
                    {event.title}
                </div>
                {!isSmallDuration && (
                    <div className="event-time">
                        {format(event.start, 'h:mm a')} - {format(event.end, 'h:mm a')}
                    </div>
                )}

                {/* Resize Handle */}
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
