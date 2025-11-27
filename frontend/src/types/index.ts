export interface Event {
    id: string;
    title: string;
    start: Date;
    end: Date;
    type: 'show' | 'rehearsal' | 'maintenance' | 'movie' | 'game' | 'activity' | 'music' | 'headliner' | 'other';
    color?: string;
}

export interface ItineraryItem {
    day: number;
    date: string;
    location: string;
    time: string;
}
