import React from 'react';
import { useDroppable } from '@dnd-kit/core';
import clsx from 'clsx';

interface DayColumnProps {
    date: Date;
    id?: string;
    children?: React.ReactNode;
}

export const DayColumn: React.FC<DayColumnProps> = ({ date, id, children }) => {
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
        >
            {/* Hour Dividers (Visual only, matches TimeColumn) */}
            {Array.from({ length: 24 }).map((_, i) => (
                <div key={i} className="grid-line-hour" style={{ borderBottom: 'none', borderRight: 'none' }}></div>
            ))}

            {/* Events */}
            {children}
        </div>
    );
};
