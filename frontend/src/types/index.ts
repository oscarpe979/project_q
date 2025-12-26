export interface Event {
    id: string;
    title: string;
    start: Date;
    end: Date;
    color?: string;
    timeDisplay?: string;
    notes?: string;
    type?: string;
    endIsLate?: boolean;  // True if end time should display as "Late"
}

export interface ItineraryItem {
    day: number;
    date: string;
    location: string;
    time: string;
    arrival?: string;
    departure?: string;
}

export interface OtherVenueShow {
    venue: string;
    shows: {
        date: string; // YYYY-MM-DD
        title: string;
        time: string; // Display string e.g. "8:00 pm & 10:00 pm"
    }[];
}

export interface HistoryState {
    events: Event[];
    itinerary: ItineraryItem[];
    otherVenueShows: OtherVenueShow[];
}
