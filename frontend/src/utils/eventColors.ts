import type { Event } from '../types';

// Color Palette
const COLORS = {
    PRODUCTION_SHOW_1: '#962f2fff', // Vivid Red
    PRODUCTION_SHOW_2: '#234da8ff', // Vivid Blue
    PRODUCTION_SHOW_3: '#820080', // Deep Purple
    HEADLINER: '#84f0e6',         // Bright Teal
    MOVIE: '#E1BEE7',             // Light Purple
    GAME_SHOW: '#f7be59',         // Vivid Orange
    ACTIVITY: '#BBDEFB',          // Light Blue
    MUSIC: '#9bfa9e',             // Bright Green
    OTHER: '#e3ded3',             // Warm Grey
};

export const assignEventColors = (events: Event[]): Event[] => {
    const productionShows = new Set<string>();
    const assignedProductionColors = new Map<string, string>();

    // First pass: Identify unique production shows
    events.forEach(event => {
        if (event.type === 'show') {
            productionShows.add(event.title);
        }
    });

    // Assign colors to production shows
    const uniqueShows = Array.from(productionShows);
    uniqueShows.forEach((title, index) => {
        let color = COLORS.PRODUCTION_SHOW_1;
        if (index === 1) color = COLORS.PRODUCTION_SHOW_2;
        if (index >= 2) color = COLORS.PRODUCTION_SHOW_3;
        assignedProductionColors.set(title, color);
    });

    // Second pass: Assign colors to all events
    return events.map(event => {
        let color = COLORS.OTHER;

        switch (event.type) {
            case 'show':
                color = assignedProductionColors.get(event.title) || COLORS.PRODUCTION_SHOW_1;
                break;
            case 'headliner':
                color = COLORS.HEADLINER;
                break;
            case 'movie':
                color = COLORS.MOVIE;
                break;
            case 'game':
                color = COLORS.GAME_SHOW;
                break;
            case 'activity':
                color = COLORS.ACTIVITY;
                break;
            case 'music':
                color = COLORS.MUSIC;
                break;
            case 'rehearsal':
            case 'maintenance':
            case 'other':
            default:
                color = COLORS.OTHER;
                break;
        }

        return { ...event, color };
    });
};

export const getContrastColor = (hexColor?: string): string => {
    if (!hexColor) return '#111827';

    // Remove hash and alpha if present
    const hex = hexColor.replace('#', '').substring(0, 6);

    const r = parseInt(hex.substr(0, 2), 16);
    const g = parseInt(hex.substr(2, 2), 16);
    const b = parseInt(hex.substr(4, 2), 16);

    // Calculate relative luminance
    const yiq = ((r * 299) + (g * 587) + (b * 114)) / 1000;

    return (yiq >= 128) ? '#111827' : '#ffffff';
};
