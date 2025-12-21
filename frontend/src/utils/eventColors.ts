import type { Event } from '../types';

// Color Palette
export const COLORS = {
    PRODUCTION_SHOW_1: '#963333ff', // Vivid Red
    PRODUCTION_SHOW_2: '#7e46beff', // Vivid Blue
    PRODUCTION_SHOW_3: '#820080', // Deep Purple
    HEADLINER: '#84f0e6',         // Bright Teal
    MOVIE: '#E1BEE7',             // Light Purple
    GAME_SHOW: '#f3b344ff',         // Vivid Orange
    ACTIVITY: '#BBDEFB',          // Light Blues
    MUSIC: '#9bfa9e',             // Bright Green
    PARTY: '#a5e1f8ff',             // Yellow
    COMEDY: '#4dc7a2ff',            // Light Pink
    DOORS: '#000000',             // Black (for doors events)
    WARM_UP: '#A3FEFF',           // Faint Aquamarine (for warm up events)
    PRESET: '#e3ded3',            // Warm Grey (for preset events)
    STRIKE: '#e3ded3',            // Warm Grey (for strike events)
    OTHER: '#e3ded3',             // Warm Grey
};


export const getColorForType = (type: string): string => {
    switch (type?.toLowerCase()) {
        case 'show':
            // Simple rotation or hashing could go here if we want varied production colors
            // For now, default to the main red
            return COLORS.PRODUCTION_SHOW_1;
        case 'headliner':
            return COLORS.HEADLINER;
        case 'movie':
            return COLORS.MOVIE;
        case 'game':
            return COLORS.GAME_SHOW;
        case 'activity':
            return COLORS.ACTIVITY;
        case 'music':
            return COLORS.MUSIC;
        case 'party':
            return COLORS.PARTY;
        case 'comedy':
            return COLORS.COMEDY;
        case 'doors':
            return COLORS.DOORS;
        case 'warm_up':
            return COLORS.WARM_UP;
        case 'preset':
            return COLORS.PRESET;
        case 'strike':
            return COLORS.STRIKE;
        case 'rehearsal':
        case 'maintenance':
        case 'other':
        default:
            return COLORS.OTHER;
    }
};

export const assignEventColors = (events: Event[]): Event[] => {
    return events.map(event => ({
        ...event,
        color: event.color || COLORS.OTHER
    }));
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
