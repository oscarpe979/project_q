import React from 'react';

export const TimeColumn: React.FC = () => {
    // Generate time slots (07:00 to 23:30)
    const slots = Array.from({ length: 34 }, (_, i) => {
        const totalMinutes = i * 30;
        const hour = 7 + Math.floor(totalMinutes / 60);
        const minute = totalMinutes % 60;
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
