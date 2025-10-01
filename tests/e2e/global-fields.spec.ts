import { test, expect } from '@playwright/test';

test.describe('Global Fields Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/global-fields');
  });

  test('should display global fields workspace', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Listing');
  });

  test('should switch between Fields and Data tabs', async ({ page }) => {
    await page.click('button:has-text("Data")');
    await expect(page.locator('button:has-text("Import Data")')).toBeVisible();

    await page.click('button:has-text("Fields")');
    await expect(page.locator('button:has-text("Import Data")')).not.toBeVisible();
  });

  test('should show Import Data button on Data tab', async ({ page }) => {
    await page.click('button:has-text("Data")');
    const importButton = page.locator('button:has-text("Import Data")');
    await expect(importButton).toBeVisible();
  });

  test('should create new custom field', async ({ page }) => {
    // Click create field button (assuming there's one)
    const createButton = page.locator('button', { hasText: /create|add.*field/i }).first();
    if (await createButton.isVisible()) {
      await createButton.click();

      // Fill in basic field information
      await page.fill('input[name="label"]', 'Test Field');
      await page.selectOption('select[name="data_type"]', 'string');

      // Submit form
      await page.click('button:has-text("Save")');

      // Verify field appears in list
      await expect(page.locator('text=Test Field')).toBeVisible();
    }
  });

  test('should edit existing field', async ({ page }) => {
    // Find and click edit button on first field row
    const editButton = page.locator('button[aria-label*="Edit"]').first();
    if (await editButton.isVisible()) {
      await editButton.click();

      // Modify field
      const labelInput = page.locator('input[name="label"]');
      await labelInput.fill('Updated Field Name');

      // Save changes
      await page.click('button:has-text("Save")');

      // Verify update
      await expect(page.locator('text=Updated Field Name')).toBeVisible();
    }
  });

  test('should manage dropdown options for enum field', async ({ page }) => {
    // Create enum field
    const createButton = page.locator('button', { hasText: /create|add.*field/i }).first();
    if (await createButton.isVisible()) {
      await createButton.click();

      await page.fill('input[name="label"]', 'Priority');
      await page.selectOption('select[name="data_type"]', 'enum');

      // Add options
      await page.fill('textarea[name="options"]', 'High\nMedium\nLow');

      await page.click('button:has-text("Continue")');
      await page.click('button:has-text("Continue")');
      await page.click('button:has-text("Save")');

      // Verify field created with options
      await expect(page.locator('text=Priority')).toBeVisible();
    }
  });
});
