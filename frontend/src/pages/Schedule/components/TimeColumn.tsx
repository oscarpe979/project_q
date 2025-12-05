import React from 'react';

export const TimeColumn: React.FC = () => {
    // Generate time slots (07:00 to 01:00 next day = 18 hours)
    // 18 hours * 4 slots/hour = 72 slots
    const slots = Array.from({ length: 72 }, (_, i) => {
        const totalMinutes = i * 15;
        const hour = 7 + Math.floor(totalMinutes / 60);
        const minute = totalMinutes % 60;
        return { hour, minute };
    });

    return (
        <div style={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
            {slots.map(({ hour, minute }, index) => (
                <div key={index} className="time-slot">
                    <span className="time-label">
                        {(() => {
                            const normalizedHour = hour % 24;
                            const ampm = normalizedHour >= 12 ? 'pm' : 'am';
                            const displayHour = normalizedHour % 12 || 12;
                            return `${displayHour}:${minute.toString().padStart(2, '0')} ${ampm}`;
                        })()}
                    </span>
                </div>
            ))}
        </div>
    );
};
