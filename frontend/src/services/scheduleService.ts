import { authService } from './authService';
import type { Event, ItineraryItem } from '../types';

const API_URL = 'http://localhost:8000/api/schedules';

interface PublishScheduleRequest {
    voyage_number: string;
    events: {
        title: string;
        start: string; // ISO string
        end: string;   // ISO string
        type: string;
        notes?: string;
    }[];
    itinerary: {
        day: number;
        date: string;
        location: string;
        time?: string;
    }[];
}

export const scheduleService = {
    async publishSchedule(voyageNumber: string, events: Event[], itinerary: ItineraryItem[]) {
        const headers = authService.getAuthHeaders();

        const payload: PublishScheduleRequest = {
            voyage_number: voyageNumber,
            events: events.map(e => ({
                title: e.title,
                start: e.start.toISOString(),
                end: e.end.toISOString(),
                type: e.type,
                notes: e.notes // Assuming Event type has notes, if not we might need to extend it or ignore
            })),
            itinerary: itinerary.map(i => ({
                day: i.day,
                date: i.date,
                location: i.location,
                time: i.time
            }))
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
        const response = await fetch(`${API_URL}/latest`, {
            headers: headers,
        });

        if (!response.ok) {
            throw new Error('Failed to fetch latest schedule');
        }

        return response.json();
    },

    async deleteSchedule(voyageNumber: string) {
        const headers = authService.getAuthHeaders();
        const response = await fetch(`${API_URL}/${voyageNumber}`, {
            method: 'DELETE',
            headers: headers,
        });

        if (!response.ok) {
            throw new Error('Failed to delete schedule');
        }

        return response.json();
    }
};
