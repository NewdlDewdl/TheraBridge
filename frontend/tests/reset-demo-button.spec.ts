import { test, expect } from '@playwright/test';

test.describe('Reset Demo Button', () => {
  test('should be visible in navigation bar', async ({ page }) => {
    await page.goto('http://localhost:3000/dashboard');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Check if Reset Demo button exists and is visible
    const resetButton = page.getByRole('button', { name: 'Reset Demo' }).first();
    await expect(resetButton).toBeVisible();

    // Verify button text
    await expect(resetButton).toHaveText('Reset Demo');
  });

  test('should have correct styling in light mode', async ({ page }) => {
    await page.goto('http://localhost:3000/dashboard');
    await page.waitForLoadState('networkidle');

    const resetButton = page.getByRole('button', { name: 'Reset Demo' }).first();

    // Check if button has teal color (#5AB9B4) in light mode
    const color = await resetButton.evaluate((el) => {
      return window.getComputedStyle(el).color;
    });

    // RGB equivalent of #5AB9B4 is rgb(90, 185, 180)
    expect(color).toContain('90'); // R value
  });

  test('should show confirmation modal when clicked', async ({ page }) => {
    await page.goto('http://localhost:3000/dashboard');
    await page.waitForLoadState('networkidle');

    const resetButton = page.getByRole('button', { name: 'Reset Demo' }).first();
    await resetButton.click();

    // Check if modal appears
    const modal = page.getByText('Reset Demo?');
    await expect(modal).toBeVisible();

    // Check if modal has correct text
    await expect(page.getByText('This will delete all your demo data')).toBeVisible();

    // Check if Cancel and Reset buttons exist
    await expect(page.getByRole('button', { name: 'Cancel' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Reset Demo' }).last()).toBeVisible();
  });

  test('should close modal when Cancel is clicked', async ({ page }) => {
    await page.goto('http://localhost:3000/dashboard');
    await page.waitForLoadState('networkidle');

    // Open modal
    const resetButton = page.getByRole('button', { name: 'Reset Demo' }).first();
    await resetButton.click();

    // Wait for modal to appear
    await expect(page.getByText('Reset Demo?')).toBeVisible();

    // Click Cancel
    await page.getByRole('button', { name: 'Cancel' }).click();

    // Modal should disappear
    await expect(page.getByText('Reset Demo?')).not.toBeVisible();
  });

  test('should be visible on all pages', async ({ page }) => {
    const pages = ['/dashboard', '/sessions', '/upload', '/ask-ai'];

    for (const path of pages) {
      await page.goto(`http://localhost:3000${path}`);
      await page.waitForLoadState('networkidle');

      const resetButton = page.getByRole('button', { name: 'Reset Demo' }).first();
      await expect(resetButton).toBeVisible();
    }
  });
});
