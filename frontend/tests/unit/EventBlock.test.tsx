import { render, screen } from '@testing-library/react';
import { EventBlock } from '../../src/pages/Schedule/components/EventBlock';

describe('EventBlock', () => {
    const mockEvent = {
        id: '1',
        title: 'Test Event',
        start: new Date('2023-10-27T10:00:00'),
        end: new Date('2023-10-27T11:00:00'),
        color: '#ff0000',
        venueId: 'v1',
        voyageId: 'voy1'
    };

    it('renders event title and time', () => {
        render(
            <EventBlock
                event={mockEvent}
                style={{ height: '100px', top: '0px' }}
            />
        );

        expect(screen.getByText('Test Event')).toBeInTheDocument();
        // Time format might vary based on locale, but "10:00 AM" should be present
        expect(screen.getByText(/10:00 AM/)).toBeInTheDocument();
    });
});
