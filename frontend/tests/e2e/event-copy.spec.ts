import { test, expect } from '@playwright/test';

test.describe('Event Copy with Ctrl+Drag', () => {

    test.beforeEach(async ({ page }) => {
        // Mock API to return a schedule with one event
        await page.route('**/api/schedules/', async route => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify([
                    { voyage_number: "TEST123", start_date: "2023-10-27", end_date: "2023-11-03" }
                ])
            });
        });

        await page.route('**/api/schedules/TEST123', async route => {
            if (route.request().method() === 'GET') {
                await route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify({
                        voyage_number: "TEST123",
                        events: [
                            {
                                id: "event-1",
                                title: "Test Show",
                                start: "2023-10-27T14:00:00",
                                end: "2023-10-27T15:00:00",
                                color: "#3b82f6",
                                venueId: "main-theater"
                            }
                        ],
                        itinerary: [
                            { date: "2023-10-27", location: "At Sea" }
                        ],
                        other_venue_shows: []
                    })
                });
            } else {
                await route.fallback();
            }
        });

        // Login
        await page.goto('/login');
        await page.getByLabel('Username').fill('testuser');
        await page.getByLabel('Password').fill('password');
        await page.getByRole('button', { name: 'Sign In' }).click();

        // Select the voyage
        await page.getByRole('button', { name: /New Draft|VY/ }).click();
        await page.getByText('VY TEST123').click();
        await expect(page.locator('.voyage-selector-btn')).toContainText('VY TEST123');
    });

    test('Ctrl+drag shows ghost overlay', async ({ page }) => {
        const eventBlock = page.locator('.event-block').first();
        await expect(eventBlock).toBeVisible();

        // Get initial position
        const box = await eventBlock.boundingBox();
        if (!box) throw new Error('Event block not found');

        // Start Ctrl+drag
        await page.keyboard.down('Control');
        await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
        await page.mouse.down();
        await page.mouse.move(box.x + box.width / 2, box.y + 100, { steps: 5 });

        // Ghost overlay should appear
        await expect(page.locator('.ghost-event-overlay')).toBeVisible();

        // Original event should still be visible at original position
        await expect(eventBlock).toBeVisible();

        await page.mouse.up();
        await page.keyboard.up('Control');
    });

    test('Ctrl+drag creates a copy of the event', async ({ page }) => {
        // Count initial events
        const initialEventCount = await page.locator('.event-block').count();
        expect(initialEventCount).toBe(1);

        const eventBlock = page.locator('.event-block').first();
        const box = await eventBlock.boundingBox();
        if (!box) throw new Error('Event block not found');

        // Ctrl+drag to new position
        await page.keyboard.down('Control');
        await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
        await page.mouse.down();
        await page.mouse.move(box.x + box.width / 2, box.y + 200, { steps: 10 });
        await page.mouse.up();
        await page.keyboard.up('Control');

        // Should now have 2 events (original + copy)
        await expect(page.locator('.event-block')).toHaveCount(2);
    });

    test('Normal drag moves event without copying', async ({ page }) => {
        const initialEventCount = await page.locator('.event-block').count();
        expect(initialEventCount).toBe(1);

        const eventBlock = page.locator('.event-block').first();
        const box = await eventBlock.boundingBox();
        if (!box) throw new Error('Event block not found');

        // Normal drag (no Ctrl key)
        await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
        await page.mouse.down();
        await page.mouse.move(box.x + box.width / 2, box.y + 100, { steps: 10 });
        await page.mouse.up();

        // Should still have only 1 event (no copy created)
        await expect(page.locator('.event-block')).toHaveCount(1);
    });

    test('Releasing Ctrl mid-drag cancels copy mode', async ({ page }) => {
        const initialEventCount = await page.locator('.event-block').count();
        expect(initialEventCount).toBe(1);

        const eventBlock = page.locator('.event-block').first();
        const box = await eventBlock.boundingBox();
        if (!box) throw new Error('Event block not found');

        // Start Ctrl+drag
        await page.keyboard.down('Control');
        await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
        await page.mouse.down();
        await page.mouse.move(box.x + box.width / 2, box.y + 100, { steps: 5 });

        // Ghost should be visible
        await expect(page.locator('.ghost-event-overlay')).toBeVisible();

        // Release Ctrl - ghost should disappear
        await page.keyboard.up('Control');
        await page.waitForTimeout(100);
        await expect(page.locator('.ghost-event-overlay')).not.toBeVisible();

        // Complete drag
        await page.mouse.up();

        // Should still have only 1 event (copy was cancelled)
        await expect(page.locator('.event-block')).toHaveCount(1);
    });
});
