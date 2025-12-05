import { test, expect } from '@playwright/test';

test('Full Login Flow', async ({ page }) => {
    await page.goto('/login');

    // Fill in credentials
    await page.getByLabel('Username').fill('testuser');
    await page.getByLabel('Password').fill('password');

    // Click sign in
    await page.getByRole('button', { name: 'Sign In' }).click();

    // Expect to be redirected to schedule
    await expect(page).toHaveURL(/.*\/schedule/);
});
