
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { VoyageSelector } from '../../src/pages/Schedule/components/VoyageSelector';

describe('VoyageSelector', () => {
    // Mock react-virtuoso since JSDOM doesn't support layout/resize observers
    vi.mock('react-virtuoso', () => ({
        Virtuoso: ({ data, itemContent, endReached, components: _components }: any) => {
            return (
                <div data-testid="virtuoso-mock">
                    {data.map((item: any, index: number) => (
                        <div key={index}>
                            {itemContent(index, item)}
                        </div>
                    ))}
                </div>
            );
        }
    }));

    // Mock IntersectionObserver
    beforeAll(() => {
        vi.stubGlobal('IntersectionObserver', class IntersectionObserver {
            constructor(_callback: any, _options: any) { }
            observe() { }
            unobserve() { }
            disconnect() { }
        });
    });

    const mockVoyages = [
        { voyage_number: '100', start_date: '2025-01-01', end_date: '2025-01-07' },
        { voyage_number: '200', start_date: '2025-02-01', end_date: '2025-02-07' }
    ];

    it('renders and calls onSearch with debounce', async () => {
        const onSearchMock = vi.fn();
        const onSelectMock = vi.fn();

        render(
            <VoyageSelector
                voyages={mockVoyages}
                currentVoyageNumber="100"
                onSelect={onSelectMock}
                title="Test Ship"
                onSearch={onSearchMock}
            />
        );

        // Open dropdown
        const button = screen.getByRole('button', { name: /Test Ship/i });
        fireEvent.click(button);

        // Find search input
        const input = screen.getByPlaceholderText(/Deep search voyages/i);
        expect(input).toBeInTheDocument();

        // Type in search
        fireEvent.change(input, { target: { value: 'install' } });

        // Verify not called immediately (debounce)
        expect(onSearchMock).not.toHaveBeenCalled();

        // Wait for debounce (300ms)
        await waitFor(() => {
            expect(onSearchMock).toHaveBeenCalledWith('install');
        }, { timeout: 1000 });
    });

    it('clears search input when X button is clicked', async () => {
        vi.useFakeTimers();
        const onSearchMock = vi.fn();
        render(
            <VoyageSelector
                voyages={mockVoyages}
                currentVoyageNumber="100"
                onSelect={vi.fn()}
                title="Test Ship"
                onSearch={onSearchMock}
            />
        );

        // Open dropdown
        fireEvent.click(screen.getByRole('button', { name: /Test Ship/i }));

        // Type search
        const input = screen.getByPlaceholderText('Deep search voyages...');
        fireEvent.change(input, { target: { value: 'test' } });

        // Fast-forward debounce timer
        vi.advanceTimersByTime(300);

        expect(onSearchMock).toHaveBeenCalledWith('test');
        const clearButton = screen.getByLabelText('Clear search');
        fireEvent.click(clearButton);

        // Verify input is empty
        expect(input).toHaveValue('');
    });

    it('displays loading skeleton when isLoadingMore is true', () => {
        render(
            <VoyageSelector
                voyages={mockVoyages}
                currentVoyageNumber="100"
                onSelect={vi.fn()}
                title="Test Ship"
                onSearch={vi.fn()}
                onLoadMore={vi.fn()}
                isLoadingMore={true}
                hasMore={true}
            />
        );

        // Open dropdown
        fireEvent.click(screen.getByRole('button', { name: /Test Ship/i }));

        // Ensure throttle doesn't block (advance time if needed, but this test checks RENDER, no interaction)

        // Verify "View More..." button is NOT present
        expect(screen.queryByText('View More...')).not.toBeInTheDocument();

        // Verify we still see the voyages (might be 2 occurrences: header and list)
        expect(screen.getAllByText(/VY 100/).length).toBeGreaterThan(0);
    });

    it('limits initial display to 5 items', () => {
        // Create 10 mock voyages
        const manyVoyages = Array.from({ length: 10 }, (_, i) => ({
            voyage_number: `10${i}`,
            start_date: '2025-01-01',
            end_date: '2025-01-07'
        }));

        render(
            <VoyageSelector
                voyages={manyVoyages}
                currentVoyageNumber=""
                onSelect={vi.fn()}
                title="Test Ship"
                onSearch={vi.fn()} // Simulate backend mode
                onLoadMore={vi.fn()}
                hasMore={true}
            />
        );

        // Open dropdown
        fireEvent.click(screen.getByRole('button', { name: /Test Ship/i }));

        // Check visible items
        const items = screen.getAllByText(/VY 10/);
        expect(items).toHaveLength(5);
    });
});
