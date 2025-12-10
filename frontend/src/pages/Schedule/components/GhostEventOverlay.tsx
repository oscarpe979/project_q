import React from 'react';
import { format } from 'date-fns';
import type { Event } from '../../../types';
import { getContrastColor } from '../../../utils/eventColors';

const PIXELS_PER_HOUR = 100;
const SNAP_MINUTES = 5;

interface GhostEventOverlayProps {
    event: Event;
    dragDelta: { x: number; y: number };
    width: number;
    height: string;
}

export const GhostEventOverlay: React.FC<GhostEventOverlayProps> = ({
    event,
    dragDelta,
    width,
    height,
}) => {
    const SNAP_PIXELS = PIXELS_PER_HOUR / (60 / SNAP_MINUTES);
    const snappedDeltaY = Math.round(dragDelta.y / SNAP_PIXELS) * SNAP_PIXELS;
    const minutesShift = snappedDeltaY * (60 / PIXELS_PER_HOUR);
    const previewStart = new Date(event.start.getTime() + minutesShift * 60 * 1000);
    const previewEnd = new Date(event.end.getTime() + minutesShift * 60 * 1000);

    return (
        <div
            className="ghost-event-overlay"
            style={{
                width: `${width}px`,
                height: `calc(${height} - 2px)`,
                background: event.color,
                color: getContrastColor(event.color),
            }}
        >
            <span className="ghost-time">
                {format(previewStart, 'h:mm a')} - {format(previewEnd, 'h:mm a')}
            </span>
            <span className="ghost-title">{event.title}</span>
        </div>
    );
};
