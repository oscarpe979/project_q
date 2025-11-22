import React from 'react';
import { format, addDays, startOfWeek, setMinutes } from 'date-fns';
import { DndContext, useSensor, useSensors, PointerSensor } from '@dnd-kit/core';
import type { DragEndEvent } from '@dnd-kit/core';
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
                // 80px = 60 minutes => 1px = 0.75 minutes
                const minutesShift = (delta.y / 80) * 60;

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

    return (
        <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
            <div className="flex flex-col h-full">
                {/* Header Row */}
                <div className="flex border-b border-[var(--border-light)] bg-[var(--bg-panel)] sticky top-0 z-30 backdrop-blur-md">
                    <div className="w-20 flex-shrink-0 border-r border-[var(--border-light)]"></div>
                    {days.map((day) => (
                        <div key={day.toString()} className="flex-1 py-3 text-center border-r border-[var(--border-light)] last:border-r-0">
                            <div className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
                                {format(day, 'EEE')}
                            </div>
                            <div className="text-lg font-bold text-[var(--text-primary)]">
                                {format(day, 'd')}
                            </div>
                        </div>
                    ))}
                </div>

                {/* Grid Body */}
                <div className="flex flex-1 overflow-y-auto relative">
                    <TimeColumn />

                    <div className="flex flex-1 relative">
                        {/* Background Grid Lines */}
                        <div className="absolute inset-0 flex pointer-events-none">
                            {days.map((day) => (
                                <div key={`bg - ${day.toString()} `} className="flex-1 border-r border-[var(--border-light)] last:border-r-0 h-full"></div>
                            ))}
                        </div>

                        {/* Day Columns with Events */}
                        {days.map((day) => {
                            const dayEvents = events.filter(e =>
                                e.start.getDate() === day.getDate() &&
                                e.start.getMonth() === day.getMonth()
                            );

                            // Simple stacking algorithm
                            // 1. Sort by start time
                            const sortedEvents = [...dayEvents].sort((a, b) => a.start.getTime() - b.start.getTime());

                            // 2. Calculate overlaps
                            const eventsWithLayout = sortedEvents.map((event) => {
                                // Find overlapping events
                                const overlaps = sortedEvents.filter(other =>
                                    other.id !== event.id &&
                                    other.start < event.end &&
                                    other.end > event.start
                                );

                                const totalOverlaps = overlaps.length + 1;
                                // Find index among overlaps (naive approach, can be improved)
                                const overlapIndex = overlaps.filter(o => o.start.getTime() < event.start.getTime() || (o.start.getTime() === event.start.getTime() && o.id < event.id)).length;

                                const widthPercent = 95 / totalOverlaps;
                                const leftPercent = 2.5 + (overlapIndex * widthPercent);

                                // Calculate top position based on start time (80px per hour)
                                const startHour = event.start.getHours() + event.start.getMinutes() / 60;
                                const top = startHour * 80;

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
                                <DayColumn key={day.toString()} date={day}>
                                    {eventsWithLayout.map(({ event, style }) => (
                                        <EventBlock
                                            key={event.id}
                                            event={event}
                                            style={style}
                                        />
                                    ))}
                                </DayColumn>
                            );
                        })}
                    </div>
                </div>
            </div>
        </DndContext>
    );
};
