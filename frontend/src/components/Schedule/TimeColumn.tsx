import React from 'react';

export const TimeColumn: React.FC = () => {
    // Generate time slots (00:00 to 23:00)
    const hours = Array.from({ length: 24 }, (_, i) => i);

    return (
        <div className="w-20 flex-shrink-0 flex flex-col border-r border-[var(--border-light)] bg-[var(--bg-app)] select-none">
            {hours.map((hour) => (
                <div key={hour} className="h-20 relative border-b border-[var(--border-light)] last:border-b-0">
                    <span className="absolute -top-3 right-2 text-xs text-[var(--text-secondary)] font-medium bg-[var(--bg-app)] px-1">
                        {hour.toString().padStart(2, '0')}:00
                    </span>
                </div>
            ))}
        </div>
    );
};
