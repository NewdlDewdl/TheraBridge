import { test, expect } from '@playwright/test';

test.describe('Navigation Debug', () => {
  test('Test dashboard loads without errors', async ({ page }) => {
    const errors: string[] = [];

    // Capture console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    // Capture page errors
    page.on('pageerror', error => {
      errors.push(`Page Error: ${error.message}`);
    });

    await page.goto('http://localhost:3000/dashboard');
    await page.waitForTimeout(2000);

    console.log('\n=== DASHBOARD ERRORS ===');
    errors.forEach(err => console.log(err));
    console.log('======================\n');

    expect(errors.length).toBe(0);
  });

  test('Test sessions page loads without errors', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    page.on('pageerror', error => {
      errors.push(`Page Error: ${error.message}`);
    });

    await page.goto('http://localhost:3000/sessions');
    await page.waitForTimeout(2000);

    console.log('\n=== SESSIONS ERRORS ===');
    errors.forEach(err => console.log(err));
    console.log('======================\n');

    expect(errors.length).toBe(0);
  });

  test('Test upload page loads without errors', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    page.on('pageerror', error => {
      errors.push(`Page Error: ${error.message}`);
    });

    await page.goto('http://localhost:3000/upload');
    await page.waitForTimeout(2000);

    console.log('\n=== UPLOAD ERRORS ===');
    errors.forEach(err => console.log(err));
    console.log('======================\n');

    expect(errors.length).toBe(0);
  });

  test('Test ask-ai page loads without errors', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    page.on('pageerror', error => {
      errors.push(`Page Error: ${error.message}`);
    });

    await page.goto('http://localhost:3000/ask-ai');
    await page.waitForTimeout(2000);

    console.log('\n=== ASK-AI ERRORS ===');
    errors.forEach(err => console.log(err));
    console.log('======================\n');

    expect(errors.length).toBe(0);
  });

  test('Test navigation between pages', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    page.on('pageerror', error => {
      errors.push(`Page Error: ${error.message}`);
    });

    // Start on dashboard
    await page.goto('http://localhost:3000/dashboard');
    await page.waitForTimeout(1000);

    // Click Sessions
    console.log('\n=== Clicking Sessions ===');
    await page.click('text=Sessions');
    await page.waitForTimeout(1000);

    // Click Upload
    console.log('=== Clicking Upload ===');
    await page.click('text=Upload');
    await page.waitForTimeout(1000);

    // Click Ask AI
    console.log('=== Clicking Ask AI ===');
    await page.click('text=Ask AI');
    await page.waitForTimeout(1000);

    // Click Dashboard
    console.log('=== Clicking Dashboard ===');
    await page.click('text=Dashboard');
    await page.waitForTimeout(1000);

    console.log('\n=== NAVIGATION ERRORS ===');
    errors.forEach(err => console.log(err));
    console.log('=========================\n');

    expect(errors.length).toBe(0);
  });
});
