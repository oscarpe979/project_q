import React from 'react';
import { useDraggable } from '@dnd-kit/core';
import clsx from 'clsx';

export interface Event {
    id: string;
    title: string;
    start: Date;
    end: Date;
    type: 'show' | 'rehearsal' | 'maintenance' | 'other';
}

interface EventBlockProps {
    event: Event;
    style?: React.CSSProperties;
}

export const EventBlock: React.FC<EventBlockProps> = ({ event, style }) => {
    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
        id: event.id,
        data: { event },
    });

    const transformStyle = transform ? {
        transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
    } : undefined;

    // Calculate height based on duration (assuming 80px per hour)
    const durationHours = (event.end.getTime() - event.start.getTime()) / (1000 * 60 * 60);
    const height = durationHours * 80;

    // Color mapping based on type (using CSS variables)
    const colorClass = {
        show: 'bg-[var(--event-blue)] text-[var(--event-blue-text)] border-[var(--event-blue-text)]',
        rehearsal: 'bg-[var(--event-purple)] text-[var(--event-purple-text)] border-[var(--event-purple-text)]',
        maintenance: 'bg-[var(--event-orange)] text-[var(--event-orange-text)] border-[var(--event-orange-text)]',
        other: 'bg-[var(--event-green)] text-[var(--event-green-text)] border-[var(--event-green-text)]',
    }[event.type];

    // Resize Handle Draggable
    const {
        attributes: resizeAttrs,
        listeners: resizeListeners,
        setNodeRef: setResizeRef,
        transform: resizeTransform,
        isDragging: isResizing
    } = useDraggable({
        id: `${event.id}-resize`,
        data: { event, type: 'resize' },
    });

    // Visual feedback for resizing (preview height change)
    // Note: This is a simple preview; for smoother UX we might want to adjust the height directly
    const resizeY = resizeTransform ? resizeTransform.y : 0;
    const displayHeight = Math.max(20, height + resizeY);

    return (
        <div
            ref={setNodeRef}
            style={{
                ...style,
                ...transformStyle,
                height: `${isResizing ? displayHeight : height}px`,
                zIndex: isDragging || isResizing ? 50 : 10,
            }}
            {...listeners}
            {...attributes}
            className={clsx(
                "absolute w-[95%] left-[2.5%] rounded-md p-2 text-xs font-medium border-l-4 shadow-sm cursor-grab active:cursor-grabbing transition-shadow select-none overflow-hidden",
                colorClass,
                (isDragging || isResizing) ? "shadow-xl opacity-80 ring-2 ring-offset-2 ring-blue-400" : "hover:shadow-md"
            )}
        >
            <div className="font-bold truncate">{event.title}</div>
            <div className="opacity-75 truncate">
                {event.start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} -
                {event.end.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>

            {/* Resize Handle */}
            <div
                ref={setResizeRef}
                {...resizeListeners}
                {...resizeAttrs}
                className="absolute bottom-0 left-0 w-full h-3 cursor-ns-resize flex items-center justify-center hover:bg-black/10 group"
                onClick={(e) => e.stopPropagation()} // Prevent click through
            >
                <div className="w-8 h-1 rounded-full bg-black/20 group-hover:bg-black/30"></div>
            </div>
        </div>
    );
};
