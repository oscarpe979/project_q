import { renderHook, act, waitFor } from '@testing-library/react';
import { useScheduleState } from '../../src/hooks/useScheduleState';
import { scheduleService } from '../../src/services/scheduleService';
import { vi, describe, it, expect, beforeEach } from 'vitest';

// Mock scheduleService
vi.mock('../../src/services/scheduleService', () => ({
    scheduleService: {
        getShipVenues: vi.fn().mockResolvedValue([]),
        getSchedules: vi.fn(),
        getLatestSchedule: vi.fn().mockResolvedValue({}),
        getScheduleByVoyage: vi.fn().mockResolvedValue({}),
    }
}));

describe('useScheduleState Pagination Logic', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('handles 21 items correctly (limit 20)', async () => {
        // Mock 21 items total
        const allItems = Array.from({ length: 21 }, (_, i) => ({
            voyage_number: `V${i + 1}`,
            start_date: '2025-01-01',
            end_date: '2025-01-07'
        }));

        // Mock getSchedules implementation
        // It receives (search, skip, limit)
        (scheduleService.getSchedules as any).mockImplementation((_search: string, skip: number, limit: number) => {
            const slice = allItems.slice(skip, skip + limit);
            return Promise.resolve(slice);
        });

        const { result } = renderHook(() => useScheduleState());

        // Initial Load
        await act(async () => {
            // This triggers the first fetch in the hook? No, hook doesn't auto-fetch in useEffect?
            // Checking hook code... line 62 loads venues. Doesn't load schedules.
            // Component calls loadSchedules.
            await result.current.loadSchedules('');
        });

        // 1st Fetch: Limit 20. Skip 0.
        // Should return 20 items.
        expect(result.current.voyages.length).toBe(20);
        expect(result.current.hasMore).toBe(true);
        expect(result.current.voyages[19].voyage_number).toBe('V20');

        // Load More
        await act(async () => {
            result.current.loadMoreSchedules();
        });

        // 2nd Fetch: Limit 20. Skip 20.
        // Should return 1 item (V21).
        // Verify straightforward append logic works.

        expect(result.current.voyages.length).toBe(21);
        expect(result.current.voyages[20].voyage_number).toBe('V21');
        expect(result.current.hasMore).toBe(false);
    });
});
