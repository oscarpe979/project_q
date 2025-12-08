import React from 'react';
import { useDroppable } from '@dnd-kit/core';
import clsx from 'clsx';

interface DayColumnProps {
    date: Date;
    id?: string;
    children?: React.ReactNode;
    onClick?: (e: React.MouseEvent<HTMLDivElement>) => void;
}

export const DayColumn: React.FC<DayColumnProps> = ({ date, id, children, onClick }) => {
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
        >
            {/* Hour Dividers (Visual only, matches TimeColumn) */}
            {Array.from({ length: 17 }).map((_, i) => (
                <div key={i} className="grid-line-hour" style={{ borderBottom: 'none', borderRight: 'none' }}></div>
            ))}

            {/* Events */}
            {children}
        </div>
    );
};
