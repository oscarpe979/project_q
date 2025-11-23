import React, { useMemo } from 'react';
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
        useSensor(PointerSensor)
    );

    const handleDragEnd = (event: DragEndEvent) => {
        const { active, delta, over } = event;
        const activeId = String(active.id);
        const isResize = activeId.endsWith('-resize');
        const isResizeTop = activeId.endsWith('-resize-top');
        const eventId = isResize
            ? activeId.replace('-resize', '')
            : isResizeTop
                ? activeId.replace('-resize-top', '')
                : activeId;

        setEvents((prev) => prev.map((e) => {
            if (e.id === eventId) {
                // Calculate time shift in minutes
                // 100px = 60 minutes => 1px = 0.6 minutes
                const minutesShift = delta.y * (60 / 100);

                // Snap to nearest 15 minutes
                const snappedMinutes = Math.round(minutesShift / 15) * 15;

                if (isResizeTop) {
                    // Update Start Time (dragging top edge)
                    const newStart = addDays(setMinutes(e.start, e.start.getMinutes() + snappedMinutes), 0);
                    // Prevent start time after end time
                    if (newStart >= e.end) return e;

                    return { ...e, start: newStart };
                } else if (isResize) {
                    // Update End Time (dragging bottom edge)
                    const newEnd = addDays(setMinutes(e.end, e.end.getMinutes() + snappedMinutes), 0);
                    // Prevent end time before start time
                    if (newEnd <= e.start) return e;

                    return { ...e, end: newEnd };
                } else {
                    // Move Event (Start & End)
                    let newStart = addDays(setMinutes(e.start, e.start.getMinutes() + snappedMinutes), 0);
                    let newEnd = addDays(setMinutes(e.end, e.end.getMinutes() + snappedMinutes), 0);

                    // Check if dropped into a different day column
                    if (over && over.id !== activeId) {
                        const targetDayStr = String(over.id);
                        // Check if it's a day column (ISO string format)
                        if (targetDayStr.includes('T')) {
                            const targetDay = new Date(targetDayStr);
                            const currentDay = new Date(e.start);
                            currentDay.setHours(0, 0, 0, 0);
                            targetDay.setHours(0, 0, 0, 0);

                            // Calculate day difference
                            const dayDiff = Math.round((targetDay.getTime() - currentDay.getTime()) / (1000 * 60 * 60 * 24));

                            if (dayDiff !== 0) {
                                newStart = addDays(newStart, dayDiff);
                                newEnd = addDays(newEnd, dayDiff);
                            }
                        }
                    }

                    return {
                        ...e,
                        start: newStart,
                        end: newEnd,
                    };
                }
            }
            return e;
        }));
    };

    // Calculate layout for all events once (memoized for performance)
    const allEventsWithLayout = useMemo(() => events.map((event) => {
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

        // Calculate width: full column width divided by overlaps, minus 2px total (1px margin each side)
        const widthCalc = totalOverlaps === 1
            ? 'calc(100% - 2px)'
            : `calc(${100 / totalOverlaps}% - 2px)`;
        const leftCalc = totalOverlaps === 1
            ? '1px'
            : `calc(${(100 / totalOverlaps) * overlapIndex}% + 1px)`;

        // Calculate top position based on start time (100px per hour)
        // Start at 7am
        const startHour = event.start.getHours() + event.start.getMinutes() / 60;
        const top = (startHour - 7) * 100;

        // Calculate height based on duration (100px per hour)
        const durationMinutes = (event.end.getTime() - event.start.getTime()) / (1000 * 60);
        const height = (durationMinutes / 60) * 100;

        return {
            event,
            style: {
                top: `${top}px`,
                height: `${height}px`,
                width: widthCalc,
                left: leftCalc,
            }
        };
    }), [events]);

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
                            {Array.from({ length: 17 }).map((_, i) => (
                                <div key={i} className="grid-line-hour">
                                    {/* 15-minute sub-lines */}
                                    <div className="grid-line-15" style={{ top: '25px' }}></div>
                                    <div className="grid-line-15" style={{ top: '50px' }}></div>
                                    <div className="grid-line-15" style={{ top: '75px' }}></div>
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
                                            item.event.start >= day &&
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
