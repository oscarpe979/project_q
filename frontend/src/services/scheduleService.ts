import { authService } from './authService';
import type { Event, ItineraryItem, OtherVenueShow } from '../types';

const API_URL = 'http://localhost:8000/api/schedules/';

interface PublishScheduleRequest {
    voyage_number: string;
    events: {
        title: string;
        start: string; // ISO string
        end: string;   // ISO string
        color?: string;
        time_display?: string;
        notes?: string;
        type?: string;
    }[];
    itinerary: {
        day: number;
        date: string;
        location: string;
        time?: string;
        arrival?: string;
        departure?: string;
    }[];
    other_venue_shows?: {
        venue: string;
        date: string;
        title: string;
        time: string;
    }[];
}

// Helper to format date as local ISO string (YYYY-MM-DDTHH:mm:ss)
const toLocalISOString = (date: Date) => {
    const pad = (num: number) => num.toString().padStart(2, '0');
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
};
export const scheduleService = {
    async publishSchedule(voyageNumber: string, events: Event[], itinerary: ItineraryItem[], otherVenueShows?: OtherVenueShow[], originalVoyageNumber?: string) {
        const headers = authService.getAuthHeaders();

        const payload: PublishScheduleRequest & { original_voyage_number?: string } = {
            voyage_number: voyageNumber,
            original_voyage_number: originalVoyageNumber,
            events: events.map(e => ({
                title: e.title,
                start: toLocalISOString(e.start),
                end: toLocalISOString(e.end),
                color: e.color,
                time_display: e.timeDisplay,
                notes: e.notes,
                type: e.type,
            })),
            itinerary: itinerary.map(i => ({
                day: i.day,
                date: i.date,
                location: i.location,
                time: i.time,
                arrival: i.arrival,
                departure: i.departure
            })),
            other_venue_shows: otherVenueShows?.flatMap(venue =>
                venue.shows.map(show => ({
                    venue: venue.venue,
                    date: show.date,
                    title: show.title,
                    time: show.time
                }))
            )
        };

        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                ...headers,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to publish schedule');
        }

        return response.json();
    },

    async getLatestSchedule() {
        const headers = authService.getAuthHeaders();
        const response = await fetch(`${API_URL}latest`, {
            headers: headers,
        });

        if (!response.ok) {
            throw new Error('Failed to fetch latest schedule');
        }

        return response.json();
    },

    async deleteSchedule(voyageNumber: string) {
        const headers = authService.getAuthHeaders();
        const response = await fetch(`${API_URL}${voyageNumber}`, {
            method: 'DELETE',
            headers: headers,
        });

        if (!response.ok) {
            throw new Error('Failed to delete schedule');
        }

        return response.json();
    },

    async getSchedules(search?: string, skip: number = 0, limit: number = 20, signal?: AbortSignal) {
        const headers = authService.getAuthHeaders();
        const url = new URL(API_URL);
        if (search) {
            url.searchParams.append('search', search);
        }
        url.searchParams.append('skip', skip.toString());
        url.searchParams.append('limit', limit.toString());

        const response = await fetch(url.toString(), {
            headers: headers,
            signal // Pass the signal to fetch
        });
        if (!response.ok) {
            throw new Error('Failed to fetch schedules');
        }
        return response.json();
    },

    async getScheduleByVoyage(voyageNumber: string) {
        const headers = authService.getAuthHeaders();
        const response = await fetch(`${API_URL}${voyageNumber}`, {
            headers: headers,
        });

        if (!response.ok) {
            throw new Error('Failed to fetch schedule');
        }

        return response.json();
    },

    async getShipVenues() {
        const headers = authService.getAuthHeaders();
        const response = await fetch(`${API_URL}venues`, {
            headers: headers,
        });

        if (!response.ok) {
            throw new Error('Failed to fetch ship venues');
        }

        return response.json();
    },

};
