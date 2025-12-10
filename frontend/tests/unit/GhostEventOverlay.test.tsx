import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { GhostEventOverlay } from '../../src/pages/Schedule/components/GhostEventOverlay';

describe('GhostEventOverlay', () => {
    const mockEvent = {
        id: 'event-1',
        title: 'Test Event',
        start: new Date('2023-10-27T10:00:00'),
        end: new Date('2023-10-27T11:00:00'),
        color: '#3b82f6',
        venueId: 'venue-1',
        voyageId: 'voyage-1'
    };

    it('renders event title', () => {
        render(
            <GhostEventOverlay
                event={mockEvent}
                dragDelta={{ x: 0, y: 0 }}
                width={200}
                height="100px"
            />
        );

        expect(screen.getByText('Test Event')).toBeInTheDocument();
    });

    it('renders original times when no drag delta', () => {
        render(
            <GhostEventOverlay
                event={mockEvent}
                dragDelta={{ x: 0, y: 0 }}
                width={200}
                height="100px"
            />
        );

        // Time should show original event time: 10:00 AM - 11:00 AM
        expect(screen.getByText(/10:00 AM/)).toBeInTheDocument();
        expect(screen.getByText(/11:00 AM/)).toBeInTheDocument();
    });

    it('calculates shifted times based on drag delta', () => {
        // delta.y of 100 pixels = 1 hour shift (PIXELS_PER_HOUR = 100)
        render(
            <GhostEventOverlay
                event={mockEvent}
                dragDelta={{ x: 0, y: 100 }}
                width={200}
                height="100px"
            />
        );

        // Time should be shifted by 1 hour: 11:00 AM - 12:00 PM
        expect(screen.getByText(/11:00 AM/)).toBeInTheDocument();
        expect(screen.getByText(/12:00 PM/)).toBeInTheDocument();
    });

    it('snaps times to 5-minute intervals', () => {
        // delta.y of 12 pixels would be ~7.2 minutes, should snap to 5 minutes
        // 100px = 60min, so 12px = 7.2min => snapped to 5min
        render(
            <GhostEventOverlay
                event={mockEvent}
                dragDelta={{ x: 0, y: 8.33 }} // ~5 minutes worth
                width={200}
                height="100px"
            />
        );

        // Time should be shifted by 5 minutes: 10:05 AM - 11:05 AM
        expect(screen.getByText(/10:05 AM/)).toBeInTheDocument();
        expect(screen.getByText(/11:05 AM/)).toBeInTheDocument();
    });

    it('applies width and height from props', () => {
        const { container } = render(
            <GhostEventOverlay
                event={mockEvent}
                dragDelta={{ x: 0, y: 0 }}
                width={250}
                height="150px"
            />
        );

        const overlay = container.querySelector('.ghost-event-overlay');
        expect(overlay).toHaveStyle({ width: '250px' });
        expect(overlay).toHaveStyle({ height: 'calc(150px - 2px)' });
    });

    it('applies event color as background', () => {
        const { container } = render(
            <GhostEventOverlay
                event={mockEvent}
                dragDelta={{ x: 0, y: 0 }}
                width={200}
                height="100px"
            />
        );

        const overlay = container.querySelector('.ghost-event-overlay');
        expect(overlay).toHaveStyle({ background: '#3b82f6' });
    });
});
