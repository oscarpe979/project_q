import React from 'react';

export const TimeColumn: React.FC = () => {
    // Generate time slots (00:00 to 23:30)
    const slots = Array.from({ length: 48 }, (_, i) => {
        const hour = Math.floor(i / 2);
        const minute = (i % 2) * 30;
        return { hour, minute };
    });

    return (
        <div style={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
            {slots.map(({ hour, minute }, index) => (
                <div key={index} className="time-slot">
                    <span className="time-label">
                        {hour.toString().padStart(2, '0')}:{minute.toString().padStart(2, '0')}
                    </span>
                </div>
            ))}
        </div>
    );
};
