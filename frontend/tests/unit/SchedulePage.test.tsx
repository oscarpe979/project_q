import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SchedulePage } from '../../src/pages/Schedule/SchedulePage';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { scheduleService } from '../../src/services/scheduleService';

// Mock scheduleService
vi.mock('../../src/services/scheduleService', () => ({
    scheduleService: {
        getSchedules: vi.fn(),
        getShipVenues: vi.fn(),
        getLatestSchedule: vi.fn(),
        publishSchedule: vi.fn(),
        deleteSchedule: vi.fn(),
    }
}));

// Mock authService
vi.mock('../../src/services/authService', () => ({
    authService: {
        getCurrentUser: () => ({ id: 1, venue_id: 1, ship_id: 1, username: 'test_user' }),
        isAuthenticated: () => true
    }
}));

// Mock ScheduleGrid to avoid DnD complexity
vi.mock('../../src/pages/Schedule/components/ScheduleGrid', () => ({
    ScheduleGrid: () => <div data-testid="schedule-grid">Schedule Grid Placeholder</div>
}));

// Helper to render
const renderPage = () => {
    const mockUser = { name: 'Test User', role: 'admin', username: 'test_user' };
    const mockLogout = vi.fn();
    return render(
        <BrowserRouter>
            <SchedulePage user={mockUser} onLogout={mockLogout} />
        </BrowserRouter>
    );
};

describe('SchedulePage - Safe Publish', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        // Default mocks
        (scheduleService.getSchedules as any).mockResolvedValue([]);
        (scheduleService.getShipVenues as any).mockResolvedValue([]);
        (scheduleService.getLatestSchedule as any).mockResolvedValue({ voyage_number: 'NEW', events: [], itinerary: [] });
    });

    it('Frontend Collision: Shows error immediately if voyage exists in loaded list', async () => {
        // 1. Mock getSchedules to return an existing voyage "123"
        (scheduleService.getSchedules as any).mockResolvedValue([
            { voyage_number: '123' }
        ]);

        renderPage();

        // Wait for page to load
        await waitFor(() => expect(screen.getByTestId('schedule-grid')).toBeInTheDocument());

        // 2. Click Publish
        const publishButton = screen.getByRole('button', { name: /publish/i });
        fireEvent.click(publishButton);

        // 3. Modal opens. Input "123".
        const input = screen.getByDisplayValue(/new/i); // Initially "NEW" from latest or empty
        fireEvent.change(input, { target: { value: '123' } });

        // 4. Click Confirm
        // The modal actions might be within a portal or dialog. 
        // We look for the "Publish" button inside the modal actions.
        const confirmButton = screen.getByRole('button', { name: 'Publish' });
        fireEvent.click(confirmButton);

        // 5. Verify Error Appears WITHOUT calling service
        expect(await screen.findByText(/already exists/i)).toBeInTheDocument();
        expect(scheduleService.publishSchedule).not.toHaveBeenCalled();
    });

    it('Backend Collision: Shows error if API returns 409', async () => {
        // 1. Mock empty schedules list (so frontend check passes)
        (scheduleService.getSchedules as any).mockResolvedValue([]);

        // 2. Mock publishSchedule to fail with "already exists" (backend 409)
        (scheduleService.publishSchedule as any).mockRejectedValue(new Error('Voyage "123" already exists.'));

        renderPage();
        await waitFor(() => expect(screen.getByTestId('schedule-grid')).toBeInTheDocument());

        // 3. Open Modal and Publish "123"
        const publishButton = screen.getByRole('button', { name: /publish/i });
        fireEvent.click(publishButton);

        const input = screen.getByDisplayValue(/new/i);
        fireEvent.change(input, { target: { value: '123' } });

        const confirmButton = screen.getByRole('button', { name: 'Publish' });
        fireEvent.click(confirmButton);

        // 4. Verify Service Called AND Error Shown
        // Service SHOULD be called now because frontend list didn't have "123"
        await waitFor(() => expect(scheduleService.publishSchedule).toHaveBeenCalled());

        // Error should appear
        expect(await screen.findByText(/already exists/i)).toBeInTheDocument();
    });

    it('Success Flow: Closes modal and shows success', async () => {
        (scheduleService.getSchedules as any).mockResolvedValue([]);
        (scheduleService.publishSchedule as any).mockResolvedValue({ message: 'Success' });

        renderPage();
        await waitFor(() => expect(screen.getByTestId('schedule-grid')).toBeInTheDocument());

        const publishButton = screen.getByRole('button', { name: /publish/i });
        fireEvent.click(publishButton);

        const input = screen.getByDisplayValue(/new/i);
        fireEvent.change(input, { target: { value: '999' } });

        const confirmButton = screen.getByRole('button', { name: 'Publish' });
        fireEvent.click(confirmButton);

        // Verify service called
        await waitFor(() => expect(scheduleService.publishSchedule).toHaveBeenCalled());

        // Verify success feedback (modal closes or success message)
        // Check for success modal text "Schedule Successfully Published"
        expect(await screen.findByText(/Schedule Saved!/i)).toBeInTheDocument();
    });
});
