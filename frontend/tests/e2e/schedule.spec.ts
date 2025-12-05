
import { test, expect } from '@playwright/test';

test('View and Delete Schedule (Mocked)', async ({ page }) => {
    // Mock delete endpoint (Generic fallback for schedules)
    await page.route('**/api/schedules/*', async route => {
        const method = route.request().method();
        const url = route.request().url();
        console.log(`Intercepted ${method} ${url} `);

        if (method === 'DELETE' && url.includes('V123')) {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({ message: "Deleted" })
            });
        } else if (method === 'GET' && url.includes('V123')) {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    voyage_number: "V123",
                    events: [],
                    itinerary: [],
                    other_venue_shows: []
                })
            });
        } else {
            await route.fallback();
        }
    });

    // Mock the schedules list endpoint (Specific)
    await page.route('**/api/schedules/', async route => {
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify([
                { voyage_number: "V123", start_date: "2023-10-27", end_date: "2023-11-03" }
            ])
        });
    });

    // Login
    await page.goto('/login');
    await page.getByLabel('Username').fill('testuser');
    await page.getByLabel('Password').fill('password');
    await page.getByRole('button', { name: 'Sign In' }).click();

    // Check if schedule is visible
    // We expect to see "V123" in the list.
    // Assuming there is a "Select Voyage" button or list.
    // We need to find where the list is rendered.
    // Let's look for text "V123".
    // Open the voyage selector dropdown
    await page.getByRole('button', { name: /New Draft|VY/ }).click();

    // Check if schedule is visible in the list and click it
    await expect(page.getByText('VY V123')).toBeVisible();
    await page.getByText('VY V123').click();

    // Wait for the voyage to be loaded and selected
    await expect(page.locator('.voyage-selector-btn')).toContainText('VY V123');

    // Test Delete
    // 1. Click "View Options" dropdown
    await page.getByRole('button', { name: 'View Options' }).click();

    // 2. Click "Delete Schedule" in the menu
    await page.getByRole('button', { name: 'Delete Schedule' }).click();

    // 3. Confirm deletion in the modal
    // We need to type the voyage number "V123" into the input
    await page.locator('.delete-voyage-input').fill('V123');

    await page.getByRole('button', { name: 'Delete', exact: true }).click();

    // 4. Verify success message
    // Wait for delete modal to close
    await expect(page.locator('.delete-modal-header')).not.toBeVisible();

    // Enable console logging from the browser
    page.on('console', msg => console.log(`BROWSER: ${msg.text()}`));

    // Check for success modal
    await expect(page.locator('.success-title')).toHaveText('Schedule Deleted');
    await page.getByRole('button', { name: 'Close' }).click();
});
