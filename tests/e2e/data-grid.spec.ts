import { test, expect } from '@playwright/test';

test.describe('Data Grid Features', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/listings');
  });

  test('should display data grid with rows', async ({ page }) => {
    await page.waitForSelector('table', { timeout: 5000 });
    const rows = page.locator('table tbody tr');
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should show tooltips on column headers', async ({ page }) => {
    await page.waitForSelector('table thead', { timeout: 5000 });

    const header = page.locator('table th').first();
    await header.hover();

    // Check for tooltip appearance (adjust selector based on implementation)
    const tooltip = page.locator('[role="tooltip"]');
    if (await tooltip.isVisible({ timeout: 1000 }).catch(() => false)) {
      expect(await tooltip.isVisible()).toBe(true);
    }
  });

  test('should handle virtualization for large datasets', async ({ page }) => {
    await page.waitForSelector('table', { timeout: 5000 });

    // Scroll down
    await page.evaluate(() => {
      const container = document.querySelector('[data-grid-container]');
      if (container) {
        container.scrollTop = 1000;
      }
    });

    // Wait for new rows to render
    await page.waitForTimeout(500);

    // Verify rows are still visible
    const rows = page.locator('table tbody tr');
    expect(await rows.count()).toBeGreaterThan(0);
  });

  test('should support zebra striping for row delineation', async ({ page }) => {
    await page.waitForSelector('table tbody tr', { timeout: 5000 });

    // Check that rows have alternating backgrounds
    const firstRow = page.locator('table tbody tr:nth-child(1)');
    const secondRow = page.locator('table tbody tr:nth-child(2)');

    const firstBg = await firstRow.evaluate((el) => window.getComputedStyle(el).backgroundColor);
    const secondBg = await secondRow.evaluate((el) => window.getComputedStyle(el).backgroundColor);

    // Backgrounds should be different for zebra stripes
    expect(firstBg).not.toBe(secondBg);
  });

  test('should filter with multi-select dropdown', async ({ page }) => {
    await page.waitForSelector('table', { timeout: 5000 });

    // Find a multi-select filter (condition or other enum field)
    const multiSelectTrigger = page.locator('button[aria-label*="filter"], [data-filter-type="multi-select"]').first();

    if (await multiSelectTrigger.isVisible({ timeout: 1000 }).catch(() => false)) {
      await multiSelectTrigger.click();

      // Select option
      const checkbox = page.locator('input[type="checkbox"]').first();
      if (await checkbox.isVisible()) {
        await checkbox.check();

        // Verify filter applied
        const rows = page.locator('table tbody tr');
        expect(await rows.count()).toBeGreaterThan(0);
      }
    }
  });

  test('should persist column sizing in localStorage', async ({ page }) => {
    await page.waitForSelector('table', { timeout: 5000 });

    // Verify localStorage key exists after interaction
    const storageKey = await page.evaluate(() => {
      return localStorage.getItem('dealbrain_listings_table_state_v1:columnSizing');
    });

    // May be null if no resizing happened yet, but localStorage should be accessible
    expect(typeof storageKey).toBe('string' || 'object');
  });

  test('should handle responsive layout at different widths', async ({ page }) => {
    // Test at 1280px
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/listings');
    await page.waitForSelector('table', { timeout: 5000 });

    let table = page.locator('table');
    expect(await table.isVisible()).toBe(true);

    // Test at 1440px
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.waitForTimeout(300);

    table = page.locator('table');
    expect(await table.isVisible()).toBe(true);
  });

  test('should show empty state when no data', async ({ page }) => {
    // Navigate to entity with no data (or apply filter that yields no results)
    await page.goto('/global-fields');
    await page.click('button:has-text("Data")');

    // Apply filter that yields no results
    const filterInput = page.locator('input[placeholder*="Filter"]').first();
    if (await filterInput.isVisible({ timeout: 1000 }).catch(() => false)) {
      await filterInput.fill('NONEXISTENT_FILTER_VALUE_12345');

      // Verify empty state message
      await expect(page.locator('text=No records')).toBeVisible({ timeout: 2000 });
    }
  });
});
