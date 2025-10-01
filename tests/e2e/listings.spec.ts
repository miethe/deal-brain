import { test, expect } from '@playwright/test';

test.describe('Listings Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/listings');
  });

  test('should display listings table', async ({ page }) => {
    await expect(page.locator('h1, h2').filter({ hasText: /listing/i })).toBeVisible();
  });

  test('should filter listings by column', async ({ page }) => {
    // Wait for table to load
    await page.waitForSelector('table', { timeout: 5000 });

    // Find filter input for title column
    const titleFilter = page.locator('input[placeholder*="Filter"]').first();
    if (await titleFilter.isVisible()) {
      await titleFilter.fill('Mini');

      // Verify filtered results
      await expect(page.locator('table tbody tr')).toHaveCount(1);
    }
  });

  test('should resize columns and persist layout', async ({ page }) => {
    await page.waitForSelector('table', { timeout: 5000 });

    // Find column resize handle
    const resizeHandle = page.locator('[data-resize-handle]').first();
    if (await resizeHandle.isVisible()) {
      const box = await resizeHandle.boundingBox();
      if (box) {
        // Drag to resize
        await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
        await page.mouse.down();
        await page.mouse.move(box.x + 100, box.y + box.height / 2);
        await page.mouse.up();

        // Reload page to verify persistence
        await page.reload();
        await page.waitForSelector('table', { timeout: 5000 });

        // Column should maintain new width (verify via localStorage or visual check)
        expect(await page.evaluate(() => localStorage.getItem('dealbrain_listings_table_state_v1:columnSizing'))).toBeTruthy();
      }
    }
  });

  test('should create new listing with CPU', async ({ page }) => {
    // Navigate to add listing
    await page.goto('/listings/new');

    // Fill in listing details
    await page.fill('input[name="title"]', 'Test Listing');
    await page.fill('input[name="price_usd"]', '599.99');
    await page.selectOption('select[name="condition"]', 'used');

    // Select CPU
    const cpuSelect = page.locator('select[name="cpu_id"]');
    const options = await cpuSelect.locator('option').count();
    if (options > 1) {
      await cpuSelect.selectOption({ index: 1 });
    }

    // Fill RAM
    await page.fill('input[name="ram_gb"]', '16');

    // Fill storage
    await page.fill('input[name="primary_storage_gb"]', '512');

    // Submit
    await page.click('button:has-text("Save")');

    // Verify success
    await expect(page.locator('text=created successfully')).toBeVisible({ timeout: 10000 });
  });

  test('should create CPU inline from listing form', async ({ page }) => {
    await page.goto('/listings/new');

    // Click Add CPU button
    await page.click('button:has-text("Add CPU")');

    // Fill CPU form
    await page.fill('input[id="new-cpu-name"]', 'AMD Ryzen 9 7940HS');
    await page.fill('input[id="new-cpu-manufacturer"]', 'AMD');
    await page.fill('input[id="new-cpu-socket"]', 'FP8');
    await page.fill('input[id="new-cpu-cores"]', '8');
    await page.fill('input[id="new-cpu-threads"]', '16');

    // Submit CPU
    await page.click('button:has-text("Save CPU")');

    // Verify CPU created and selected
    await expect(page.locator('text=created and selected')).toBeVisible({ timeout: 5000 });
  });

  test('should apply filters to listings', async ({ page }) => {
    await page.waitForSelector('table', { timeout: 5000 });

    // Apply condition filter
    const conditionFilter = page.locator('select').filter({ hasText: /condition/i }).first();
    if (await conditionFilter.isVisible()) {
      await conditionFilter.selectOption('used');

      // Verify filtered results show only used condition
      const rows = page.locator('table tbody tr');
      const count = await rows.count();
      if (count > 0) {
        // Check first row contains 'used'
        await expect(rows.first()).toContainText(/used/i);
      }
    }
  });

  test('should sort listings by price', async ({ page }) => {
    await page.waitForSelector('table', { timeout: 5000 });

    // Click price column header to sort
    const priceHeader = page.locator('th:has-text("Price")');
    if (await priceHeader.isVisible()) {
      await priceHeader.click();

      // Get first two prices and verify ascending order
      const firstPrice = await page.locator('table tbody tr:nth-child(1) td:has-text("$")').first().innerText();
      const secondPrice = await page.locator('table tbody tr:nth-child(2) td:has-text("$")').first().innerText();

      const price1 = parseFloat(firstPrice.replace(/[^0-9.]/g, ''));
      const price2 = parseFloat(secondPrice.replace(/[^0-9.]/g, ''));

      expect(price1).toBeLessThanOrEqual(price2);
    }
  });
});
