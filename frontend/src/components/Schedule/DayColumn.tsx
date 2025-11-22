import React from 'react';
import { useDroppable } from '@dnd-kit/core';
import clsx from 'clsx';

interface DayColumnProps {
    date: Date;
    children?: React.ReactNode;
}

export const DayColumn: React.FC<DayColumnProps> = ({ date, children }) => {
    const { setNodeRef, isOver } = useDroppable({
        id: `day-${date.toISOString()}`,
        data: { date },
    });

    return (
        <div
            ref={setNodeRef}
            className={clsx(
                "flex-1 h-full relative transition-colors duration-200",
                isOver ? "bg-blue-50/50" : ""
            )}
        >
            {/* Hour Dividers (Visual only, matches TimeColumn) */}
            {Array.from({ length: 24 }).map((_, i) => (
                <div key={i} className="h-20 border-b border-[var(--border-light)] last:border-b-0 box-border"></div>
            ))}

            {/* Events */}
            {children}
        </div>
    );
};
