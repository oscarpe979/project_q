export interface Event {
    id: string;
    title: string;
    start: Date;
    end: Date;
    type: 'show' | 'rehearsal' | 'maintenance' | 'movie' | 'game' | 'activity' | 'music' | 'party' | 'comedy' | 'headliner' | 'other';
    color?: string;
    timeDisplay?: string;
    notes?: string;
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
