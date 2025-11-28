import React, { useMemo } from 'react';
import { format, addDays, startOfWeek, setMinutes } from 'date-fns';
import { DndContext, useSensor, useSensors, PointerSensor } from '@dnd-kit/core';
import { Edit2 } from 'lucide-react';
import type { DragEndEvent } from '@dnd-kit/core';

import { TimeColumn } from './TimeColumn';
import { DayColumn } from './DayColumn';
import { EventBlock } from './EventBlock';
import { DatePicker } from '../UI/DatePicker';
import type { Event, ItineraryItem } from '../../types';

interface ScheduleGridProps {
    events: Event[];
    setEvents: React.Dispatch<React.SetStateAction<Event[]>>;
    itinerary?: ItineraryItem[];
    onDateChange?: (dayIndex: number, newDate: Date) => void;
}

const PIXELS_PER_HOUR = 100;
const START_HOUR = 7;
const SNAP_MINUTES = 5;
const HOURS_COUNT = 18; // 07:00 to 01:00 next day

interface DayHeaderCellProps {
    day: Date;
    info?: ItineraryItem;
    index: number;
    onDateChange?: (dayIndex: number, newDate: Date) => void;
    isOpen: boolean;
    onToggle: () => void;
}

const DayHeaderCell: React.FC<DayHeaderCellProps> = ({ day, info, index, onDateChange, isOpen, onToggle }) => {
    const handleDateClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        onToggle();
    };

    const handleDateChange = (newDate: Date | null) => {
        if (newDate && onDateChange) {
            onDateChange(index, newDate);
        }
        // Close picker after selection (handled by parent toggling off or explicit close if needed, 
        // but here we just want to ensure it closes. The parent toggle logic handles the open/close state.
        // Actually, if we select a date, we want to close it. 
        // We can call onToggle() if it's currently open, or we can have a specific onClose prop.
        // But onToggle works if we know it's open.
        if (isOpen) {
            onToggle();
        }
    };

    return (
        <div className="day-header-cell">
            <div className="header-row-day-number">DAY {info ? info.day : index + 1}</div>
            <div className="header-row-day-name">{format(day, 'EEEE')}</div>
            <div className="header-row-date relative group/date">
                <span>{format(day, 'd-MMM-yy')}</span>
                {onDateChange && (
                    <>
                        <span className="pencil-spacer">
                            <span
                                role="button"
                                className="edit-icon-btn"
                                onPointerDown={(e) => e.stopPropagation()}
                                onClick={handleDateClick}
                            >
                                <Edit2 size={10} className="edit-icon-svg" />
                            </span>
                        </span>
                        {isOpen && (
                            <DatePicker
                                value={day}
                                onChange={handleDateChange}
                                onClose={onToggle}
                            />
                        )}
                    </>
                )}
            </div>
            <div className="header-row-location">{info ? info.location : 'AT SEA'}</div>
            <div className="header-row-time">{info ? info.time : '\u00A0'}</div>
        </div>
    );
};

export const ScheduleGrid: React.FC<ScheduleGridProps> = ({ events, setEvents, itinerary = [], onDateChange }) => {
    const [activeDatePickerIndex, setActiveDatePickerIndex] = React.useState<number | null>(null);

    const days = useMemo(() => {
        if (itinerary.length > 0) {
            return itinerary.map(item => {
                // Create date at local midnight to avoid timezone issues with UTC parsing
                const [year, month, day] = item.date.split('-').map(Number);
                return new Date(year, month - 1, day);
            });
        }
        const startDate = startOfWeek(new Date(), { weekStartsOn: 1 });
        return Array.from({ length: 7 }, (_, i) => addDays(startDate, i));
    }, [itinerary]);

    const sensors = useSensors(
        useSensor(PointerSensor)
    );

    const handleUpdateEvent = (eventId: string, updates: { title?: string; timeDisplay?: string }) => {
        setEvents(prev => prev.map(e =>
            e.id === eventId ? { ...e, ...updates } : e
        ));
    };

    const handleDragEnd = (event: DragEndEvent) => {
        const { active, delta, over } = event;
        const activeId = String(active.id);
        const isResizeBottom = activeId.endsWith('-resize-bottom');
        const isResizeTop = activeId.endsWith('-resize-top');
        const eventId = isResizeBottom
            ? activeId.replace('-resize-bottom', '')
            : isResizeTop
                ? activeId.replace('-resize-top', '')
                : activeId;

        setEvents((prev) => prev.map((e) => {
            if (e.id === eventId) {
                // Calculate time shift in minutes
                const minutesShift = delta.y * (60 / PIXELS_PER_HOUR);

                // Snap to nearest SNAP_MINUTES
                const snappedMinutes = Math.round(minutesShift / SNAP_MINUTES) * SNAP_MINUTES;

                if (isResizeTop) {
                    // Update Start Time (dragging top edge)
                    let newStart = addDays(setMinutes(e.start, e.start.getMinutes() + snappedMinutes), 0);

                    // Check for inversion (dragged past end time)
                    if (newStart >= e.end) return e;

                    // Enforce minimum 15 minute duration by clamping
                    const durationMinutes = (e.end.getTime() - newStart.getTime()) / (1000 * 60);
                    if (durationMinutes < 15) {
                        newStart = new Date(e.end.getTime() - 15 * 60 * 1000);
                    }

                    return { ...e, start: newStart, timeDisplay: undefined };
                } else if (isResizeBottom) {
                    // Update End Time (dragging bottom edge)
                    let newEnd = addDays(setMinutes(e.end, e.end.getMinutes() + snappedMinutes), 0);

                    // Check for inversion (dragged past start time)
                    if (newEnd <= e.start) return e;

                    // Enforce minimum 15 minute duration by clamping
                    const durationMinutes = (newEnd.getTime() - e.start.getTime()) / (1000 * 60);
                    if (durationMinutes < 15) {
                        newEnd = new Date(e.start.getTime() + 15 * 60 * 1000);
                    }

                    return { ...e, end: newEnd, timeDisplay: undefined };
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

                            // Calculate "Visual Day" of the event
                            // If event starts < 04:00, it belongs to the previous visual day
                            const currentVisualDay = new Date(e.start);
                            if (currentVisualDay.getHours() < 4) {
                                currentVisualDay.setDate(currentVisualDay.getDate() - 1);
                            }
                            currentVisualDay.setHours(0, 0, 0, 0);
                            targetDay.setHours(0, 0, 0, 0);

                            // Calculate day difference based on Visual Day
                            const dayDiff = Math.round((targetDay.getTime() - currentVisualDay.getTime()) / (1000 * 60 * 60 * 24));

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
                        timeDisplay: undefined
                    };
                }
            }
            return e;
        }));
    };

    // Helper to get the "Visual Day" for an event (grouping late night events with previous day)
    const getVisualDay = (date: Date) => {
        const d = new Date(date);
        if (d.getHours() < 4) {
            d.setDate(d.getDate() - 1);
        }
        d.setHours(0, 0, 0, 0);
        return d.getTime();
    };

    // Calculate layout for all events once (memoized for performance)
    const allEventsWithLayout = useMemo(() => events.map((event) => {
        // Find overlapping events for this specific event
        const overlaps = events.filter(other =>
            other.id !== event.id &&
            other.start < event.end &&
            other.end > event.start &&
            // Check overlap considering the visual day
            getVisualDay(other.start) === getVisualDay(event.start)
        );

        const totalOverlaps = overlaps.length + 1;
        // Find index among overlaps (naive approach, can be improved)
        const overlapIndex = overlaps.filter(o => o.start.getTime() < event.start.getTime() || (o.start.getTime() === event.start.getTime() && o.id < event.id)).length;

        // Calculate width: full column width divided by overlaps
        const widthCalc = `${100 / totalOverlaps}%`;
        const leftCalc = `${(100 / totalOverlaps) * overlapIndex}%`;

        // Calculate top position based on start time
        const startHour = event.start.getHours() + event.start.getMinutes() / 60;
        const top = (startHour - START_HOUR) * PIXELS_PER_HOUR;

        // Calculate height based on duration
        const durationMinutes = (event.end.getTime() - event.start.getTime()) / (1000 * 60);
        let height = (durationMinutes / 60) * PIXELS_PER_HOUR;

        // CLAMPING LOGIC
        const maxGridHeight = HOURS_COUNT * PIXELS_PER_HOUR;
        const isLate = (top + height) > maxGridHeight;

        if (isLate) {
            height = Math.max(0, maxGridHeight - top);
        }

        return {
            event,
            isLate,
            style: {
                top: `${top}px`,
                height: `${height}px`,
                width: widthCalc,
                left: leftCalc,
            }
        };
    }), [events]);

    return (
        <div className="schedule-container custom-scrollbar">
            {/* Days Header */}
            <div
                className="days-header"
            >
                <div className="time-spacer">
                    <div className="spacer-label spacer-day">DAY</div>
                    <div className="spacer-label spacer-date">DATE</div>
                    <div className="spacer-label spacer-port">PORT</div>
                    <div className="spacer-label spacer-empty"></div>
                </div>
                <div
                    className="days-grid"
                    style={{ gridTemplateColumns: `repeat(${days.length}, minmax(210px, 250px))` }}
                >
                    {days.map((day, i) => (
                        <DayHeaderCell
                            key={i}
                            day={day}
                            info={itinerary[i]}
                            index={i}
                            onDateChange={onDateChange}
                            isOpen={activeDatePickerIndex === i}
                            onToggle={() => setActiveDatePickerIndex(activeDatePickerIndex === i ? null : i)}
                        />
                    ))}
                </div>
                <div className="time-spacer-right">
                    <div className="spacer-label spacer-day">DAY</div>
                    <div className="spacer-label spacer-date">DATE</div>
                    <div className="spacer-label spacer-port">PORT</div>
                    <div className="spacer-label spacer-empty"></div>
                </div>
            </div>

            {/* Main Grid */}
            <div
                className="grid-body"
            >
                <div
                    className="grid-content"
                    style={{ height: `${HOURS_COUNT * PIXELS_PER_HOUR}px` }}
                >
                    <div className="time-column">
                        <TimeColumn />
                    </div>

                    <div
                        className="events-grid"
                        style={{ gridTemplateColumns: `repeat(${days.length}, minmax(210px, 250px))` }}
                    >
                        {/* Horizontal Grid Lines */}
                        <div className="grid-lines">
                            {Array.from({ length: HOURS_COUNT }).map((_, i) => (
                                <div key={i} className="grid-line-hour">
                                    {/* 5-minute sub-lines */}
                                    {Array.from({ length: 11 }).map((_, j) => {
                                        const minutes = (j + 1) * 5;
                                        const top = (minutes / 60) * PIXELS_PER_HOUR - 1;
                                        const is15Min = minutes % 15 === 0;
                                        return (
                                            <div
                                                key={j}
                                                className={is15Min ? "grid-line-15" : "grid-line-5"}
                                                style={{ top: `${top}px` }}
                                            ></div>
                                        );
                                    })}
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
                                        .filter(item => {
                                            const eventStart = item.event.start;
                                            const nextDay = addDays(day, 1);

                                            // Standard case: starts today, BUT exclude early morning hours (00:00 - 04:00)
                                            // because those belong to the previous visual day
                                            const startsToday = eventStart >= day && eventStart < nextDay && eventStart.getHours() >= 4;

                                            // Late night case: starts tomorrow early morning (e.g. 00:00 - 04:00)
                                            // Only if it is considered "late night" of THIS day.
                                            // We define late night as < 04:00 on the IMMEDIATE next day
                                            const startsTomorrowEarly = eventStart >= nextDay && eventStart < addDays(nextDay, 1) && eventStart.getHours() < 4;

                                            return startsToday || startsTomorrowEarly;
                                        })
                                        .map(({ event, style, isLate }) => {
                                            // Adjust style for late night events
                                            let finalStyle = { ...style };
                                            let finalIsLate = isLate;

                                            // Check if this is a "late night" event relative to the column day
                                            if (event.start.getDate() !== day.getDate()) {
                                                // It must be a late night event (e.g. 00:00 start)
                                                // Re-calculate top
                                                const startHour = event.start.getHours() + event.start.getMinutes() / 60;
                                                const adjustedHour = startHour + 24; // Treat 00:00 as 24:00
                                                const newTop = (adjustedHour - START_HOUR) * PIXELS_PER_HOUR;

                                                finalStyle.top = `${newTop}px`;

                                                // Re-calculate clamping
                                                const maxGridHeight = HOURS_COUNT * PIXELS_PER_HOUR;
                                                const durationMinutes = (event.end.getTime() - event.start.getTime()) / (1000 * 60);
                                                const heightVal = (durationMinutes / 60) * PIXELS_PER_HOUR;

                                                if (newTop + heightVal > maxGridHeight) {
                                                    const newHeight = maxGridHeight - newTop;
                                                    finalStyle.height = `${Math.max(0, newHeight)}px`;
                                                    finalIsLate = true;
                                                } else {
                                                    finalStyle.height = `${heightVal}px`;
                                                    finalIsLate = false;
                                                }
                                            }

                                            return (
                                                <EventBlock
                                                    key={event.id}
                                                    event={event}
                                                    style={finalStyle}
                                                    isLate={finalIsLate}
                                                    onUpdate={handleUpdateEvent}
                                                />
                                            );
                                        })}
                                </DayColumn>
                            ))}
                        </DndContext>
                    </div>

                    <div className="time-column-right">
                        <TimeColumn />
                    </div>
                </div>
            </div>
        </div>
    );
};
