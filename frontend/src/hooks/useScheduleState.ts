import { useState, useEffect, useCallback, useRef } from 'react';
import { scheduleService } from '../services/scheduleService';
import { assignEventColors } from '../utils/eventColors';
import type { Event, ItineraryItem, OtherVenueShow, HistoryState } from '../types';

const MAX_HISTORY = 30;

function formatTimeDisplay(arrival?: string, departure?: string): string {
    const formatSingleTime = (t?: string) => {
        if (!t || t.trim().toLowerCase() === 'null') return null;
        const [hours, minutes] = t.split(':').map(Number);
        if (!isNaN(hours) && !isNaN(minutes)) {
            const date = new Date();
            date.setHours(hours, minutes);
            return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true }).toLowerCase();
        }
        return t;
    };

    const arr = formatSingleTime(arrival);
    const dep = formatSingleTime(departure);

    if (arr && dep) return `${arr} - ${dep}`;
    if (arr) return `Arrival ${arr}`;
    if (dep) return `Departure ${dep}`;
    return '';
}

const generateDefaultItinerary = (): ItineraryItem[] => {
    const today = new Date();
    const getFormattedDate = (offset: number) => {
        const date = new Date(today);
        date.setDate(today.getDate() + offset);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };

    return [
        { day: 1, date: getFormattedDate(0), location: 'MIAMI', time: '' },
        { day: 2, date: getFormattedDate(1), location: 'PERFECT DAY COCO CAY', time: '' },
        { day: 3, date: getFormattedDate(2), location: 'NASSAU', time: '' },
        { day: 4, date: getFormattedDate(3), location: 'CRUISING', time: '' },
    ];
};

export function useScheduleState() {
    const [shipVenues, setShipVenues] = useState<{ id: number; name: string }[]>([]);
    const [currentVoyageNumber, setCurrentVoyageNumber] = useState<string>('');
    const [isNewDraft, setIsNewDraft] = useState(false);

    useEffect(() => {
        const loadInitialData = async () => {
            try {
                // Fetch venues
                const venues = await scheduleService.getShipVenues();
                setShipVenues(venues);
            } catch (error) {
                console.error("Failed to load ship venues", error);
            }
        };
        loadInitialData();
    }, []);

    const [itinerary, setItinerary] = useState<ItineraryItem[]>(generateDefaultItinerary);
    const [events, setEvents] = useState<Event[]>([]);
    const [otherVenueShows, setOtherVenueShows] = useState<OtherVenueShow[]>([]);
    const [voyages, setVoyages] = useState<{ voyage_number: string; start_date: string; end_date: string }[]>([]);

    const [originalEvents, setOriginalEvents] = useState<Event[]>([]);
    const [originalItinerary, setOriginalItinerary] = useState<ItineraryItem[]>([]);
    const [originalOtherVenueShows, setOriginalOtherVenueShows] = useState<OtherVenueShow[]>([]);
    const [isModified, setIsModified] = useState(false);

    // Undo/Redo State
    const [history, setHistory] = useState<HistoryState[]>([]);
    const [historyIndex, setHistoryIndex] = useState(-1);

    // Helper to check if events are equal
    const areEventsEqual = useCallback((arr1: Event[], arr2: Event[]) => {
        if (arr1.length !== arr2.length) return false;
        const sorted1 = [...arr1].sort((a, b) => a.id.localeCompare(b.id));
        const sorted2 = [...arr2].sort((a, b) => a.id.localeCompare(b.id));

        return sorted1.every((e1, i) => {
            const e2 = sorted2[i];
            return (
                e1.id === e2.id &&
                e1.title === e2.title &&
                e1.start.getTime() === e2.start.getTime() &&
                e1.end.getTime() === e2.end.getTime() &&
                e1.color === e2.color &&
                e1.notes === e2.notes &&
                (e1.timeDisplay === e2.timeDisplay || (!e1.timeDisplay && !e2.timeDisplay))
            );
        });
    }, []);

    // Check for modifications
    useEffect(() => {
        const eventsChanged = !areEventsEqual(events, originalEvents);
        const itineraryChanged = JSON.stringify(itinerary) !== JSON.stringify(originalItinerary);
        const otherShowsChanged = JSON.stringify(otherVenueShows) !== JSON.stringify(originalOtherVenueShows);
        setIsModified(eventsChanged || itineraryChanged || otherShowsChanged);
    }, [events, itinerary, otherVenueShows, originalEvents, originalItinerary, originalOtherVenueShows, areEventsEqual]);

    // Sync shipVenues with otherVenueShows
    useEffect(() => {
        if (shipVenues.length > 0) {
            setOtherVenueShows(prevShows => {
                const newShows = [...prevShows];
                let changed = false;

                shipVenues.forEach(venue => {
                    if (!newShows.find(s => s.venue === venue.name)) {
                        newShows.push({ venue: venue.name, shows: [] });
                        changed = true;
                    }
                });

                if (changed) return newShows;
                return prevShows;
            });
        }
    }, [shipVenues]);

    // History Management
    const addToHistory = useCallback((newState: HistoryState) => {
        setHistory(prev => {
            const newHistory = prev.slice(0, historyIndex + 1);
            const updatedHistory = [...newHistory, newState];
            if (updatedHistory.length > MAX_HISTORY) {
                updatedHistory.shift();
            }
            return updatedHistory;
        });
        setHistoryIndex(prev => Math.min(prev + 1, MAX_HISTORY - 1));
    }, [historyIndex]);

    const initializeHistory = useCallback((initialEvents: Event[], initialItinerary: ItineraryItem[], initialShows: OtherVenueShow[]) => {
        const initialState: HistoryState = {
            events: JSON.parse(JSON.stringify(initialEvents)),
            itinerary: JSON.parse(JSON.stringify(initialItinerary)),
            otherVenueShows: JSON.parse(JSON.stringify(initialShows))
        };
        setHistory([initialState]);
        setHistoryIndex(0);
    }, []);

    // Initialize history on first load if empty
    useEffect(() => {
        if (history.length === 0 && events.length > 0) {
            initializeHistory(events, itinerary, otherVenueShows);
        }
    }, []);

    const undo = useCallback(() => {
        if (historyIndex > 0) {
            const prevState = history[historyIndex - 1];
            const restoredEvents = prevState.events.map(e => ({
                ...e,
                start: new Date(e.start),
                end: new Date(e.end)
            }));

            setEvents(restoredEvents);
            setItinerary(prevState.itinerary);
            setOtherVenueShows(prevState.otherVenueShows);
            setHistoryIndex(prev => prev - 1);
        }
    }, [history, historyIndex]);

    const redo = useCallback(() => {
        if (historyIndex < history.length - 1) {
            const nextState = history[historyIndex + 1];
            const restoredEvents = nextState.events.map(e => ({
                ...e,
                start: new Date(e.start),
                end: new Date(e.end)
            }));

            setEvents(restoredEvents);
            setItinerary(nextState.itinerary);
            setOtherVenueShows(nextState.otherVenueShows);
            setHistoryIndex(prev => prev + 1);
        }
    }, [history, historyIndex]);

    // Keyboard shortcuts
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
                e.preventDefault();
                undo();
            }
            if ((e.ctrlKey || e.metaKey) && e.key === 'y') {
                e.preventDefault();
                redo();
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [undo, redo]);

    const processScheduleData = useCallback((data: any) => {
        if (data.voyage_number) {
            setCurrentVoyageNumber(data.voyage_number);
        } else {
            setCurrentVoyageNumber('');
        }

        let processedEvents: Event[] = [];
        if (data.events && data.events.length > 0) {
            const newEvents: Event[] = data.events.map((e: any, index: number) => ({
                id: `loaded-${Date.now()}-${index}`,
                title: e.title,
                start: new Date(e.start),
                end: new Date(e.end),
                timeDisplay: e.time_display,
                notes: e.notes,
                color: e.color,
                type: e.type,
            }));
            processedEvents = assignEventColors(newEvents);
        }
        setEvents(processedEvents);
        setOriginalEvents(processedEvents);

        let processedItinerary: ItineraryItem[] = [];
        if (data.itinerary && data.itinerary.length > 0) {
            processedItinerary = data.itinerary.map((day: any) => ({
                day: day.day,
                date: day.date,
                location: day.location,
                time: formatTimeDisplay(day.arrival_time, day.departure_time) || day.port_times || '',
                arrival: (day.arrival_time && day.arrival_time.trim().toLowerCase() !== 'null') ? day.arrival_time : null,
                departure: (day.departure_time && day.departure_time.trim().toLowerCase() !== 'null') ? day.departure_time : null
            }));
        } else {
            processedItinerary = generateDefaultItinerary();
        }
        setItinerary(processedItinerary);
        setOriginalItinerary(processedItinerary);

        // Process other venue shows
        const grouped: { [key: string]: { date: string; title: string; time: string }[] } = {};

        // Initialize with empty lists for all ship venues (template)
        shipVenues.forEach(v => {
            grouped[v.name] = [];
        });

        if (data.other_venue_shows && data.other_venue_shows.length > 0) {
            data.other_venue_shows.forEach((show: any) => {
                if (!grouped[show.venue]) {
                    grouped[show.venue] = [];
                }
                grouped[show.venue].push({
                    date: show.date,
                    title: show.title,
                    time: show.time
                });
            });
        }

        const newOtherShows: OtherVenueShow[] = Object.keys(grouped).map(venue => ({
            venue,
            shows: grouped[venue]
        }));
        setOtherVenueShows(newOtherShows);
        setOriginalOtherVenueShows(JSON.parse(JSON.stringify(newOtherShows)));

        setIsModified(false);
        initializeHistory(processedEvents, processedItinerary, newOtherShows);
    }, [shipVenues, initializeHistory]);

    const clearSchedule = useCallback(() => {
        setEvents([]);
        setItinerary(generateDefaultItinerary());
        setOriginalEvents([]);
        setOriginalItinerary(generateDefaultItinerary());
        setCurrentVoyageNumber('');
        setIsModified(false);
        setIsNewDraft(true);

        const templateShows: OtherVenueShow[] = shipVenues.map(v => ({
            venue: v.name,
            shows: []
        }));
        setOtherVenueShows(templateShows);
        setOriginalOtherVenueShows(templateShows);
        initializeHistory([], generateDefaultItinerary(), templateShows);
    }, [shipVenues, initializeHistory]);

    const [isLoadingMore, setIsLoadingMore] = useState(false);
    const [hasMore, setHasMore] = useState(true);
    const [currentSearch, setCurrentSearch] = useState('');
    const [offset, setOffset] = useState(0);
    const LIMIT = 20;

    const abortControllerRef = useRef<AbortController | null>(null);

    const loadSchedules = useCallback(async (search?: string, isLoadMore = false) => {
        // Prevent concurrent load-more requests
        if (isLoadMore && isLoadingMore) return;

        // Cancel previous request if searching (new search term)
        if (!isLoadMore && abortControllerRef.current) {
            abortControllerRef.current.abort();
        }

        const controller = new AbortController();
        if (!isLoadMore) {
            abortControllerRef.current = controller;
        }

        if (isLoadMore) {
            setIsLoadingMore(true);
        }

        try {
            const searchParams = search !== undefined ? search : currentSearch;
            const skip = isLoadMore ? offset : 0;

            // Standard Fetch
            const data = await scheduleService.getSchedules(searchParams, skip, LIMIT, controller.signal);

            if (isLoadMore) {
                setVoyages(prev => [...prev, ...data]);
                setOffset(prev => prev + data.length);
                setHasMore(data.length === LIMIT);
            } else {
                setVoyages(data);
                setOffset(data.length);
                setHasMore(data.length === LIMIT);
                setCurrentSearch(searchParams);
                if (data.length < LIMIT) setHasMore(false);
            }
        } catch (error: any) {
            if (error.name !== 'AbortError') {
                console.error("Failed to load schedules", error);
            }
        } finally {
            if (isLoadMore) {
                setIsLoadingMore(false);
            }
            if (!isLoadMore && abortControllerRef.current === controller) {
                abortControllerRef.current = null;
            }
        }
    }, [currentSearch, offset, isLoadingMore]);

    const loadMoreSchedules = useCallback(() => {
        if (!isLoadingMore && hasMore) {
            loadSchedules(undefined, true);
        }
    }, [isLoadingMore, hasMore, loadSchedules]);

    const loadLatestSchedule = useCallback(async () => {
        try {
            const data = await scheduleService.getLatestSchedule();
            processScheduleData(data);
            setIsNewDraft(!data.voyage_number);
        } catch (error) {
            console.error("Failed to load latest schedule", error);
            clearSchedule();
        }
    }, [processScheduleData, clearSchedule]);

    const loadScheduleByVoyage = useCallback(async (voyageNumber: string) => {
        try {
            const data = await scheduleService.getScheduleByVoyage(voyageNumber);
            processScheduleData(data);
            setCurrentVoyageNumber(voyageNumber);
            setIsNewDraft(false);
        } catch (error) {
            console.error("Failed to load schedule", error);
            alert('Failed to load schedule');
        }
    }, [processScheduleData]);

    // Event Handlers
    const handleEventsChange = useCallback((newEvents: Event[] | ((prev: Event[]) => Event[])) => {
        const updatedEvents = typeof newEvents === 'function' ? newEvents(events) : newEvents;

        if (areEventsEqual(events, updatedEvents)) return;

        setEvents(updatedEvents);
        addToHistory({
            events: JSON.parse(JSON.stringify(updatedEvents)),
            itinerary: JSON.parse(JSON.stringify(itinerary)),
            otherVenueShows: JSON.parse(JSON.stringify(otherVenueShows))
        });
    }, [events, areEventsEqual, addToHistory, itinerary, otherVenueShows]);

    const handleDateChange = useCallback((dayIndex: number, newDate: Date) => {
        if (!itinerary[dayIndex]) return;

        const oldDateStr = itinerary[dayIndex].date;

        if (!oldDateStr) {
            const newItinerary = itinerary.map((item, index) => {
                const date = new Date(newDate);
                date.setDate(date.getDate() + (index - dayIndex));
                const year = date.getFullYear();
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const day = String(date.getDate()).padStart(2, '0');
                return { ...item, date: `${year}-${month}-${day}` };
            });

            setItinerary(newItinerary);
            addToHistory({
                events: JSON.parse(JSON.stringify(events)),
                itinerary: JSON.parse(JSON.stringify(newItinerary)),
                otherVenueShows: JSON.parse(JSON.stringify(otherVenueShows))
            });
            return;
        }

        const [oldYear, oldMonth, oldDay] = oldDateStr.split('-').map(Number);
        const oldDate = new Date(oldYear, oldMonth - 1, oldDay);
        oldDate.setHours(0, 0, 0, 0);
        newDate.setHours(0, 0, 0, 0);

        const diffTime = newDate.getTime() - oldDate.getTime();
        const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));

        if (diffDays === 0) return;

        const newItinerary = itinerary.map(item => {
            const [y, m, d] = item.date.split('-').map(Number);
            const date = new Date(y, m - 1, d);
            date.setDate(date.getDate() + diffDays);
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            return { ...item, date: `${year}-${month}-${day}` };
        });

        const newEvents = events.map(event => {
            const newStart = new Date(event.start);
            newStart.setDate(newStart.getDate() + diffDays);
            const newEnd = new Date(event.end);
            newEnd.setDate(newEnd.getDate() + diffDays);
            return { ...event, start: newStart, end: newEnd };
        });

        const newOtherVenueShows = otherVenueShows.map(venue => ({
            ...venue,
            shows: venue.shows.map(show => {
                const [y, m, d] = show.date.split('-').map(Number);
                const date = new Date(y, m - 1, d);
                date.setDate(date.getDate() + diffDays);
                const year = date.getFullYear();
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const day = String(date.getDate()).padStart(2, '0');
                return { ...show, date: `${year}-${month}-${day}` };
            })
        }));

        setItinerary(newItinerary);
        setEvents(newEvents);
        setOtherVenueShows(newOtherVenueShows);

        addToHistory({
            events: JSON.parse(JSON.stringify(newEvents)),
            itinerary: JSON.parse(JSON.stringify(newItinerary)),
            otherVenueShows: JSON.parse(JSON.stringify(newOtherVenueShows))
        });
    }, [itinerary, events, otherVenueShows, addToHistory]);

    const handleLocationChange = useCallback((dayIndex: number, newLocation: string) => {
        const newItinerary = [...itinerary];
        if (newItinerary[dayIndex]) {
            newItinerary[dayIndex] = { ...newItinerary[dayIndex], location: newLocation };
            setItinerary(newItinerary);
            addToHistory({
                events: JSON.parse(JSON.stringify(events)),
                itinerary: JSON.parse(JSON.stringify(newItinerary)),
                otherVenueShows: JSON.parse(JSON.stringify(otherVenueShows))
            });
        }
    }, [itinerary, events, otherVenueShows, addToHistory]);

    const handleTimeChange = useCallback((dayIndex: number, arrival: string | null, departure: string | null) => {
        const newItinerary = [...itinerary];
        if (newItinerary[dayIndex]) {
            const timeDisplay = formatTimeDisplay(arrival || undefined, departure || undefined);
            newItinerary[dayIndex] = {
                ...newItinerary[dayIndex],
                arrival: arrival || undefined,
                departure: departure || undefined,
                time: timeDisplay
            };
            setItinerary(newItinerary);
            addToHistory({
                events: JSON.parse(JSON.stringify(events)),
                itinerary: JSON.parse(JSON.stringify(newItinerary)),
                otherVenueShows: JSON.parse(JSON.stringify(otherVenueShows))
            });
            setIsModified(true);
        }
    }, [itinerary, events, otherVenueShows, addToHistory]);

    const handleOtherVenueShowUpdate = useCallback((venue: string, date: string, title: string, time: string) => {
        const newShows = [...otherVenueShows];
        const venueIndex = newShows.findIndex(v => v.venue === venue);

        if (venueIndex !== -1) {
            const currentShows = newShows[venueIndex].shows;
            const showIndex = currentShows.findIndex(s => s.date === date);
            const existingShow = showIndex !== -1 ? currentShows[showIndex] : null;

            const currentTitle = existingShow ? existingShow.title : '';
            const currentTime = existingShow ? existingShow.time : '';

            if (currentTitle === title && currentTime === time) return;

            newShows[venueIndex] = { ...newShows[venueIndex], shows: [...newShows[venueIndex].shows] };

            if (title.trim() === '' && time.trim() === '') {
                if (showIndex !== -1) {
                    newShows[venueIndex].shows.splice(showIndex, 1);
                }
            } else {
                if (showIndex !== -1) {
                    newShows[venueIndex].shows[showIndex] = { date, title, time };
                } else {
                    newShows[venueIndex].shows.push({ date, title, time });
                }
            }
        }

        setOtherVenueShows(newShows);
        addToHistory({
            events: JSON.parse(JSON.stringify(events)),
            itinerary: JSON.parse(JSON.stringify(itinerary)),
            otherVenueShows: JSON.parse(JSON.stringify(newShows))
        });
        setIsModified(true);
    }, [otherVenueShows, events, itinerary, addToHistory]);

    return {
        events,
        setEvents,
        itinerary,
        setItinerary,
        otherVenueShows,
        setOtherVenueShows,
        voyages,
        currentVoyageNumber,
        setCurrentVoyageNumber,
        isModified,
        setIsModified,
        isNewDraft,
        setIsNewDraft,
        historyIndex,
        history,
        loadSchedules,
        loadMoreSchedules,
        isLoadingMore,
        hasMore,
        loadLatestSchedule,
        loadScheduleByVoyage,
        handleEventsChange,
        handleDateChange,
        handleLocationChange,
        handleTimeChange,
        handleOtherVenueShowUpdate,
        undo,
        redo,
        clearSchedule,
        processScheduleData,
        setOriginalEvents,
        setOriginalItinerary,
        setOriginalOtherVenueShows,
        formatTimeDisplay
    };
}
