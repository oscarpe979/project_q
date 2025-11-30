import React, { useMemo } from 'react';
import { format, addDays, startOfWeek, setMinutes } from 'date-fns';
import { DndContext, useSensor, useSensors, PointerSensor } from '@dnd-kit/core';
import { Edit2 } from 'lucide-react';
import type { DragEndEvent } from '@dnd-kit/core';

import { TimeColumn } from './TimeColumn';
import { DayColumn } from './DayColumn';
import { EventBlock } from './EventBlock';
import { DatePicker } from '../UI/DatePicker';
import { FooterHighlightCell } from './FooterHighlightCell';
import type { Event, ItineraryItem, OtherVenueShow } from '../../types';

interface ScheduleGridProps {
    events: Event[];
    setEvents: React.Dispatch<React.SetStateAction<Event[]>>;
    itinerary?: ItineraryItem[];
    onDateChange?: (dayIndex: number, newDate: Date) => void;
    onLocationChange?: (dayIndex: number, newLocation: string) => void;
    otherVenueShows?: OtherVenueShow[];
    onOtherVenueShowUpdate?: (venue: string, date: string, title: string, time: string) => void;
}

const PIXELS_PER_HOUR = 100;
const START_HOUR = 7;
const SNAP_MINUTES = 5;
const HOURS_COUNT = 18; // 07:00 to 01:00 next day
const COLUMN_WIDTH_DEF = 'minmax(210px, 230px)';

interface DayHeaderCellProps {
    day: Date;
    info?: ItineraryItem;
    index: number;
    onDateChange?: (dayIndex: number, newDate: Date) => void;
    onLocationChange?: (dayIndex: number, newLocation: string) => void;
    isOpen: boolean;
    onToggle: () => void;
}

const DayHeaderCell: React.FC<DayHeaderCellProps> = ({ day, info, index, onDateChange, onLocationChange, isOpen, onToggle }) => {
    const [isEditingLocation, setIsEditingLocation] = React.useState(false);
    const [locationInput, setLocationInput] = React.useState(info ? info.location : '');
    const inputRef = React.useRef<HTMLInputElement>(null);
    const timeoutRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);

    React.useEffect(() => {
        if (info) {
            setLocationInput(info.location);
        }
    }, [info]);

    React.useEffect(() => {
        if (isEditingLocation && inputRef.current) {
            inputRef.current.focus();
        }
    }, [isEditingLocation]);

    React.useEffect(() => {
        return () => {
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
            }
        };
    }, []);

    const handleDateClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        onToggle();
    };

    const handleDateChange = (newDate: Date | null) => {
        if (newDate && onDateChange) {
            onDateChange(index, newDate);
        }
        if (isOpen) {
            onToggle();
        }
    };

    const handleLocationClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        setIsEditingLocation(true);
    };

    const handleLocationSubmit = () => {
        // Delay closing to allow "shrink back" animation (CSS transition is 0.05s)
        timeoutRef.current = setTimeout(() => {
            if (onLocationChange && locationInput !== (info ? info.location : '')) {
                onLocationChange(index, locationInput);
            }
            setIsEditingLocation(false);
        }, 50);
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') {
            e.currentTarget.blur(); // Triggers onBlur -> handleLocationSubmit
        } else if (e.key === 'Escape') {
            setLocationInput(info ? info.location : '');
            setIsEditingLocation(false);
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
            <div className="header-row-location relative group/location">
                {isEditingLocation ? (
                    <input
                        ref={inputRef}
                        type="text"
                        className="glass-input"
                        value={locationInput}
                        onChange={(e) => setLocationInput(e.target.value)}
                        onBlur={handleLocationSubmit}
                        onKeyDown={handleKeyDown}
                        onClick={(e) => e.stopPropagation()}
                    />
                ) : (
                    <>
                        <span>{info ? info.location : 'AT SEA'}</span>
                        {onLocationChange && (
                            <span className="pencil-spacer">
                                <span
                                    role="button"
                                    className="edit-icon-btn"
                                    onPointerDown={(e) => e.stopPropagation()}
                                    onClick={handleLocationClick}
                                >
                                    <Edit2 size={10} className="edit-icon-svg" />
                                </span>
                            </span>
                        )}
                    </>
                )}
            </div>
            <div className="header-row-time">{info ? info.time : '\u00A0'}</div>
        </div>
    );
};

export const ScheduleGrid: React.FC<ScheduleGridProps> = ({ events, setEvents, itinerary = [], onDateChange, onLocationChange, otherVenueShows = [], onOtherVenueShowUpdate }) => {
    const [activeDatePickerIndex, setActiveDatePickerIndex] = React.useState<number | null>(null);

    const days = useMemo(() => {
        if (itinerary.length > 0) {
            return itinerary.map(item => {
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
                const minutesShift = delta.y * (60 / PIXELS_PER_HOUR);
                const snappedMinutes = Math.round(minutesShift / SNAP_MINUTES) * SNAP_MINUTES;

                if (isResizeTop) {
                    let newStart = addDays(setMinutes(e.start, e.start.getMinutes() + snappedMinutes), 0);
                    if (newStart >= e.end) return e;
                    const durationMinutes = (e.end.getTime() - newStart.getTime()) / (1000 * 60);
                    if (durationMinutes < 15) {
                        newStart = new Date(e.end.getTime() - 15 * 60 * 1000);
                    }
                    return { ...e, start: newStart, timeDisplay: undefined };
                } else if (isResizeBottom) {
                    let newEnd = addDays(setMinutes(e.end, e.end.getMinutes() + snappedMinutes), 0);
                    if (newEnd <= e.start) return e;
                    const durationMinutes = (newEnd.getTime() - e.start.getTime()) / (1000 * 60);
                    if (durationMinutes < 15) {
                        newEnd = new Date(e.start.getTime() + 15 * 60 * 1000);
                    }
                    return { ...e, end: newEnd, timeDisplay: undefined };
                } else {
                    let newStart = addDays(setMinutes(e.start, e.start.getMinutes() + snappedMinutes), 0);
                    let newEnd = addDays(setMinutes(e.end, e.end.getMinutes() + snappedMinutes), 0);

                    if (over && over.id !== activeId) {
                        const targetDayStr = String(over.id);
                        if (targetDayStr.includes('T')) {
                            const targetDay = new Date(targetDayStr);
                            const currentVisualDay = new Date(e.start);
                            if (currentVisualDay.getHours() < 4) {
                                currentVisualDay.setDate(currentVisualDay.getDate() - 1);
                            }
                            currentVisualDay.setHours(0, 0, 0, 0);
                            targetDay.setHours(0, 0, 0, 0);
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

    const getVisualDay = (date: Date) => {
        const d = new Date(date);
        if (d.getHours() < 4) {
            d.setDate(d.getDate() - 1);
        }
        d.setHours(0, 0, 0, 0);
        return d.getTime();
    };

    const allEventsWithLayout = useMemo(() => events.map((event) => {
        const overlaps = events.filter(other =>
            other.id !== event.id &&
            other.start < event.end &&
            other.end > event.start &&
            getVisualDay(other.start) === getVisualDay(event.start)
        );

        const totalOverlaps = overlaps.length + 1;
        const overlapIndex = overlaps.filter(o => o.start.getTime() < event.start.getTime() || (o.start.getTime() === event.start.getTime() && o.id < event.id)).length;

        const widthCalc = `${100 / totalOverlaps}%`;
        const leftCalc = `${(100 / totalOverlaps) * overlapIndex}%`;

        const startHour = event.start.getHours() + event.start.getMinutes() / 60;
        const top = (startHour - START_HOUR) * PIXELS_PER_HOUR;

        const durationMinutes = (event.end.getTime() - event.start.getTime()) / (1000 * 60);
        let height = (durationMinutes / 60) * PIXELS_PER_HOUR;

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
            <div className="days-header">
                <div className="time-spacer">
                    <div className="spacer-label spacer-day">DAY</div>
                    <div className="spacer-label spacer-date">DATE</div>
                    <div className="spacer-label spacer-port">PORT</div>
                    <div className="spacer-label spacer-empty"></div>
                </div>
                <div
                    className="days-grid"
                    style={{ gridTemplateColumns: `repeat(${days.length}, ${COLUMN_WIDTH_DEF})` }}
                >
                    {days.map((day, i) => (
                        <DayHeaderCell
                            key={i}
                            day={day}
                            info={itinerary[i]}
                            index={i}
                            onDateChange={onDateChange}
                            onLocationChange={onLocationChange}
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

            <div className="grid-body">
                <div
                    className="grid-content"
                    style={{ height: `${HOURS_COUNT * PIXELS_PER_HOUR}px` }}
                >
                    <div className="time-column">
                        <TimeColumn />
                    </div>

                    <div
                        className="events-grid"
                        style={{ gridTemplateColumns: `repeat(${days.length}, ${COLUMN_WIDTH_DEF})` }}
                    >
                        <div className="grid-lines">
                            {Array.from({ length: HOURS_COUNT }).map((_, i) => (
                                <div key={i} className="grid-line-hour">
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
                                            const startsToday = eventStart >= day && eventStart < nextDay && eventStart.getHours() >= 4;
                                            const startsTomorrowEarly = eventStart >= nextDay && eventStart < addDays(nextDay, 1) && eventStart.getHours() < 4;
                                            return startsToday || startsTomorrowEarly;
                                        })
                                        .map(({ event, style, isLate }) => {
                                            let finalStyle = { ...style };
                                            let finalIsLate = isLate;
                                            if (event.start.getDate() !== day.getDate()) {
                                                const startHour = event.start.getHours() + event.start.getMinutes() / 60;
                                                const adjustedHour = startHour + 24;
                                                const newTop = (adjustedHour - START_HOUR) * PIXELS_PER_HOUR;
                                                finalStyle.top = `${newTop}px`;
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

                {/* Other Venue Shows Section */}
                {otherVenueShows.length > 0 && (
                    <div className="other-venues-section">
                        {otherVenueShows.map((venueData, vIndex) => (
                            <div key={vIndex} className="venue-row">
                                {/* Venue Name Label (Left) */}
                                <div className="venue-label left">
                                    {venueData.venue}
                                </div>

                                {/* Days Grid */}
                                <div className="venue-days-grid" style={{ display: 'grid', gridTemplateColumns: `repeat(${days.length}, ${COLUMN_WIDTH_DEF})` }}>
                                    {days.map((day, dIndex) => {
                                        const dateStr = format(day, 'yyyy-MM-dd');
                                        const show = venueData.shows.find(s => s.date === dateStr);

                                        return (
                                            <FooterHighlightCell
                                                key={dIndex}
                                                venue={venueData.venue}
                                                date={day}
                                                show={show}
                                                onUpdate={onOtherVenueShowUpdate || (() => { })}
                                            />
                                        );
                                    })}
                                </div>

                                {/* Venue Name Label (Right) */}
                                <div className="venue-label right">
                                    {venueData.venue}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};
