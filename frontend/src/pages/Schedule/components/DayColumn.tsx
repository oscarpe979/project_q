import React from 'react';
import { useDroppable } from '@dnd-kit/core';
import { ArrowDown } from 'lucide-react';
import clsx from 'clsx';

interface DayColumnProps {
    date: Date;
    id?: string;
    children?: React.ReactNode;
    onClick?: (e: React.MouseEvent<HTMLDivElement>) => void;
    onPointerDown?: (e: React.PointerEvent<HTMLDivElement>) => void;
    onPointerMove?: (e: React.PointerEvent<HTMLDivElement>) => void;
    onPointerUp?: (e: React.PointerEvent<HTMLDivElement>) => void;
    highlightRef?: (el: HTMLDivElement | null) => void;
    ghostRef?: (el: HTMLDivElement | null) => void;
    isHovered?: boolean;
}

const DayColumnComponent: React.FC<DayColumnProps> = ({
    date,
    id,
    children,
    onClick,
    onPointerDown,
    onPointerMove,
    onPointerUp,
    highlightRef,
    ghostRef,
    isHovered
}) => {
    const { setNodeRef, isOver } = useDroppable({
        id: id || `day-${date.toISOString()}`,
        data: { date },
    });

    return (
        <div
            ref={setNodeRef}
            className={clsx(
                "day-column",
                isOver && "droppable-over"
            )}
            onClick={onClick}
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp}
            style={{ position: 'relative' }}
        >
            {/* Hour Dividers */}
            {Array.from({ length: 17 }).map((_, i) => (
                <div key={i} className="grid-line-hour" style={{ borderBottom: 'none', borderRight: 'none' }}></div>
            ))}

            {/* Hover Highlight */}
            {isHovered && (
                <div
                    ref={highlightRef}
                    className="slot-highlight"
                    style={{
                        height: '1px',
                        width: '100%',
                        willChange: 'top'
                    }}
                />
            )}

            {/* Ghost Event */}
            <div
                ref={ghostRef}
                className="event-ghost"
                style={{
                    display: 'none',
                    position: 'absolute',
                    width: '100%',
                    zIndex: 10,
                    pointerEvents: 'none',
                    willChange: 'top, height'
                }}
            >
                <div className="event-ghost-content">
                    {/* Initial Drag Hint */}
                    <div className="ghost-drag-hint flex items-center gap-1 text-xs font-medium opacity-90">
                        <span>Drag to create</span>
                        <ArrowDown size={14} className="animate-bounce" />
                    </div>

                    {/* Standard Content (Hidden initially) */}
                    <div className="ghost-standard-content" style={{ display: 'none', flexDirection: 'column', alignItems: 'center', gap: '1px' }}>
                        <span className="ghost-time"></span>
                        <span className="ghost-title">New Event</span>
                    </div>
                </div>
            </div>

            {children}
        </div>
    );
};

export const DayColumn = React.memo(DayColumnComponent);
