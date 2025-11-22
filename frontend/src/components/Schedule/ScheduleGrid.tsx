import React from 'react';
import { format, addDays, startOfWeek, setMinutes } from 'date-fns';
import { DndContext, useSensor, useSensors, PointerSensor } from '@dnd-kit/core';
import type { DragEndEvent } from '@dnd-kit/core';
import clsx from 'clsx';
import { TimeColumn } from './TimeColumn';
import { DayColumn } from './DayColumn';
import { EventBlock } from './EventBlock';
import type { Event } from './EventBlock';

interface ScheduleGridProps {
    events: Event[];
    setEvents: React.Dispatch<React.SetStateAction<Event[]>>;
}

export const ScheduleGrid: React.FC<ScheduleGridProps> = ({ events, setEvents }) => {
    const startDate = startOfWeek(new Date(), { weekStartsOn: 1 });
    const days = Array.from({ length: 7 }, (_, i) => addDays(startDate, i));

    const sensors = useSensors(
        useSensor(PointerSensor, {
            activationConstraint: {
                distance: 8,
            },
        })
    );

    const handleDragEnd = (event: DragEndEvent) => {
        const { active, delta } = event;
        const activeId = String(active.id);
        const isResize = activeId.endsWith('-resize');
        const eventId = isResize ? activeId.replace('-resize', '') : activeId;

        setEvents((prev) => prev.map((e) => {
            if (e.id === eventId) {
                // Calculate time shift in minutes
                // 60px = 60 minutes => 1px = 1 minute
                const minutesShift = delta.y;

                // Snap to nearest 15 minutes
                const snappedMinutes = Math.round(minutesShift / 15) * 15;

                if (isResize) {
                    // Update End Time
                    const newEnd = addDays(setMinutes(e.end, e.end.getMinutes() + snappedMinutes), 0);
                    // Prevent end time before start time
                    if (newEnd <= e.start) return e;

                    return { ...e, end: newEnd };
                } else {
                    // Move Event (Start & End)
                    return {
                        ...e,
                        start: addDays(setMinutes(e.start, e.start.getMinutes() + snappedMinutes), 0),
                        end: addDays(setMinutes(e.end, e.end.getMinutes() + snappedMinutes), 0),
                    };
                }
            }
            return e;
        }));
    };

    // Calculate layout for all events once
    const allEventsWithLayout = events.map((event) => {
        // Find overlapping events for this specific event
        const overlaps = events.filter(other =>
            other.id !== event.id &&
            other.start < event.end &&
            other.end > event.start &&
            other.start.getDate() === event.start.getDate() && // Ensure same day
            other.start.getMonth() === event.start.getMonth()
        );

        const totalOverlaps = overlaps.length + 1;
        // Find index among overlaps (naive approach, can be improved)
        const overlapIndex = overlaps.filter(o => o.start.getTime() < event.start.getTime() || (o.start.getTime() === event.start.getTime() && o.id < event.id)).length;

        const widthPercent = 95 / totalOverlaps;
        const leftPercent = 2.5 + (overlapIndex * widthPercent);

        // Calculate top position based on start time (60px per hour)
        const startHour = event.start.getHours() + event.start.getMinutes() / 60;
        const top = startHour * 60;

        return {
            event,
            style: {
                top: `${top}px`,
                width: `${widthPercent}%`,
                left: `${leftPercent}%`,
            }
        };
    });

    return (
        <div className="schedule-container">
            {/* Days Header */}
            <div className="days-header">
                <div className="time-spacer"></div>
                <div className="days-grid">
                    {days.map((day, i) => (
                        <div key={i} className="day-header-cell">
                            <div className={clsx("day-name", i === 0 && "active-text")}>
                                {format(day, 'EEE')}
                            </div>
                            <div className={clsx("day-number", i === 0 && "active")}>
                                {format(day, 'd')}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Main Grid */}
            <div className="grid-body custom-scrollbar">
                <div className="grid-content">
                    <div className="time-column">
                        <TimeColumn />
                    </div>

                    <div className="events-grid">
                        {/* Horizontal Grid Lines */}
                        <div className="grid-lines">
                            {Array.from({ length: 24 }).map((_, i) => (
                                <div key={i} className="grid-line-hour">
                                    {/* 15-minute sub-lines */}
                                    <div className="grid-line-15" style={{ top: '15px' }}></div>
                                    <div className="grid-line-15" style={{ top: '30px' }}></div>
                                    <div className="grid-line-15" style={{ top: '45px' }}></div>
                                </div>
                            ))}
                        </div>

                        <DndContext
                            sensors={sensors}
                            onDragEnd={handleDragEnd}
                        >
                            {days.map((day) => (
                                <DayColumn key={day.toISOString()} date={day} id={day.toISOString()}>
                                    {allEventsWithLayout
                                        .filter(item =>
                                            item.event.start >= startOfWeek(day, { weekStartsOn: 1 }) &&
                                            item.event.start < addDays(day, 1)
                                        )
                                        .map(({ event, style }) => (
                                            <EventBlock
                                                key={event.id}
                                                event={event}
                                                style={style}
                                            />
                                        ))}
                                </DayColumn>
                            ))}
                        </DndContext>
                    </div>
                </div>
            </div>
        </div>
    );
};
