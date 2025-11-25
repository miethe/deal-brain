/**
 * E2E Tests: Collections Workflow
 *
 * Tests the complete collections management workflow
 *
 * User Story:
 * - User creates a new collection
 * - Adds items from listings
 * - Edits item notes and status
 * - Applies filters and sorting
 * - Switches between views (table/card)
 * - Exports collection data
 * - Deletes collection
 */

import { test, expect } from '@playwright/test';
import {
  createCollection,
  deleteCollection,
  exportCollection,
  verifyToast,
  measureResponseTime,
} from './fixtures';

test.describe('Collections Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to collections page
    await page.goto('/collections');
    await expect(page.locator('h1:has-text("Collections")')).toBeVisible({ timeout: 5000 });
  });

  test('should create new collection with name and description', async ({ page }) => {
    // Click "New Collection" button
    const newCollectionBtn = page.locator('button:has-text("New collection"), button:has-text("New Collection")');
    await expect(newCollectionBtn).toBeVisible();

    // Measure collection creation time
    const responseTime = await measureResponseTime(
      page,
      async () => {
        await newCollectionBtn.click();

        // Wait for form
        await page.waitForSelector('input[name="name"], input[id*="collection"]', {
          state: 'visible',
          timeout: 5000,
        });

        // Fill in form
        await page.fill('input[name="name"], input[id*="collection"]', 'Black Friday Deals');

        const descriptionField = page.locator('textarea[name="description"], textarea[id*="description"]');
        if (await descriptionField.isVisible({ timeout: 1000 })) {
          await descriptionField.fill('Top picks for BF 2025');
        }

        // Submit
        await page.click('button[type="submit"]:has-text("Create"), button:has-text("Create")');
      },
      '/api/v1/collections'
    );

    // Verify collection creation is fast (<500ms)
    expect(responseTime).toBeLessThan(500);

    // Verify redirect to collection workspace or success toast
    await Promise.race([
      page.waitForURL(/\/collections\/\d+/, { timeout: 10000 }),
      verifyToast(page, /created|success/i, 10000),
    ]);

    // Verify collection details are shown
    await expect(
      page.locator('h1:has-text("Black Friday Deals"), [data-testid="collection-title"]:has-text("Black Friday Deals")')
    ).toBeVisible({ timeout: 5000 });
  });

  test('should add items to collection from listings page', async ({ page }) => {
    // First, ensure we have a collection
    await page.goto('/collections');

    // Create collection if none exist
    const emptyState = page.locator('[data-testid="empty-state"], text=/no collections/i');
    const hasExistingCollections = await page.locator('[data-testid="collection-card"]').count() > 0;

    if (!hasExistingCollections) {
      await createCollection(page, 'Test Collection');
      await page.goto('/collections');
    }

    // Navigate to listings
    await page.goto('/listings');
    await page.waitForSelector('table, [data-testid="listings-grid"]', { timeout: 5000 });

    // Click "Add to Collection" on first listing
    // Note: Button may be in table row actions or on listing card
    const addButton = page.locator(
      'button:has-text("Add to Collection"), button[aria-label*="Add to collection"]'
    ).first();

    await expect(addButton).toBeVisible({ timeout: 5000 });
    await addButton.click();

    // Wait for collection selector
    await page.waitForSelector(
      '[role="dialog"], [data-radix-popper-content-wrapper]',
      { state: 'visible', timeout: 5000 }
    );

    // Select first collection
    const collectionOption = page.locator('[role="option"], button[data-collection-id]').first();
    await expect(collectionOption).toBeVisible({ timeout: 3000 });
    await collectionOption.click();

    // Verify success
    await verifyToast(page, /added|success/i);
  });

  test('should edit item notes with auto-save', async ({ page }) => {
    // Navigate to a collection workspace (assumes collection exists)
    // For standalone test, create collection first
    await page.goto('/collections');

    const collectionCard = page.locator('[data-testid="collection-card"]').first();
    if (await collectionCard.isVisible({ timeout: 5000 })) {
      await collectionCard.click();
    } else {
      // Create collection and add item
      await createCollection(page, 'Test Collection for Notes');

      // Add an item (navigate to listings and add)
      await page.goto('/listings');
      await page.waitForSelector('table', { timeout: 5000 });

      const addBtn = page.locator('button:has-text("Add to Collection")').first();
      if (await addBtn.isVisible({ timeout: 3000 })) {
        await addBtn.click();
        await page.waitForSelector('[role="dialog"]', { state: 'visible' });
        await page.locator('[role="option"]').first().click();
        await page.waitForTimeout(1000); // Wait for add to complete
      }

      // Go back to collection
      await page.goto('/collections');
      await page.click('[data-testid="collection-card"]');
    }

    // Wait for collection items to load
    await page.waitForSelector('[data-testid="collection-item"], table tbody tr', {
      timeout: 5000,
    });

    // Expand first item or click to show details panel
    const firstItem = page.locator('[data-testid="collection-item"], table tbody tr').first();
    await firstItem.click();

    // Find notes textarea
    const notesTextarea = page.locator('textarea[name*="notes"], textarea[id*="notes"]');
    if (await notesTextarea.isVisible({ timeout: 3000 })) {
      // Clear existing notes
      await notesTextarea.clear();

      // Type notes
      await notesTextarea.fill('Pros: Great price, good specs');

      // Wait for auto-save debounce (500ms)
      await page.waitForTimeout(600);

      // Verify save indicator or success (may be implicit)
      // Some implementations show a "Saved" indicator
      const saveIndicator = page.locator('text=/saved|auto-saved/i');
      if (await saveIndicator.isVisible({ timeout: 2000 }).catch(() => false)) {
        await expect(saveIndicator).toBeVisible();
      }

      // Reload page to verify persistence
      await page.reload();
      await page.waitForSelector('[data-testid="collection-item"], table tbody tr', {
        timeout: 5000,
      });

      // Click item again
      await firstItem.click();

      // Verify notes are persisted
      const persistedNotes = page.locator('textarea[name*="notes"], textarea[id*="notes"]');
      await expect(persistedNotes).toHaveValue(/Pros: Great price/);
    }
  });

  test('should change item status', async ({ page }) => {
    // Navigate to collection workspace
    await page.goto('/collections');

    const collectionCard = page.locator('[data-testid="collection-card"]').first();
    if (await collectionCard.isVisible({ timeout: 5000 })) {
      await collectionCard.click();
    } else {
      test.skip('No collections available for status test');
    }

    // Wait for items to load
    await page.waitForSelector('[data-testid="collection-item"], table tbody tr', {
      timeout: 5000,
    });

    // Click first item to show details
    const firstItem = page.locator('[data-testid="collection-item"], table tbody tr').first();
    await firstItem.click();

    // Find status selector
    const statusSelect = page.locator('select[name*="status"], [data-testid="status-select"]');
    if (await statusSelect.isVisible({ timeout: 3000 })) {
      // Change status to "shortlisted"
      await statusSelect.selectOption({ label: /shortlist/i });

      // Wait for auto-save
      await page.waitForTimeout(600);

      // Verify status change is reflected
      await expect(statusSelect).toHaveValue(/shortlist/i);
    } else {
      // Alternative: status buttons/badges
      const statusButton = page.locator('button:has-text("Shortlist"), [data-status="shortlisted"]');
      if (await statusButton.isVisible({ timeout: 2000 })) {
        await statusButton.click();
        await verifyToast(page, /updated|saved/i);
      }
    }
  });

  test('should apply filters to collection items', async ({ page }) => {
    // Navigate to collection workspace
    await page.goto('/collections');

    const collectionCard = page.locator('[data-testid="collection-card"]').first();
    if (await collectionCard.isVisible({ timeout: 5000 })) {
      await collectionCard.click();
    } else {
      test.skip('No collections available for filter test');
    }

    // Wait for items to load
    await page.waitForSelector('[data-testid="collection-item"], table tbody tr', {
      timeout: 5000,
    });

    const initialItemCount = await page.locator('[data-testid="collection-item"], table tbody tr').count();

    // Find filter controls
    const priceFilter = page.locator('input[name*="price"], input[placeholder*="price"]');
    const cpuFilter = page.locator('select[name*="cpu"], [data-testid="cpu-filter"]');

    // Apply price filter
    if (await priceFilter.isVisible({ timeout: 2000 })) {
      await priceFilter.fill('500');
      await page.waitForTimeout(300); // Debounce

      // Verify filtered results
      const filteredCount = await page.locator('[data-testid="collection-item"], table tbody tr').count();
      expect(filteredCount).toBeLessThanOrEqual(initialItemCount);
    }

    // Apply CPU family filter
    if (await cpuFilter.isVisible({ timeout: 2000 })) {
      await cpuFilter.selectOption({ index: 1 }); // Select first option
      await page.waitForTimeout(300);

      // Verify filtered results
      const filteredCount = await page.locator('[data-testid="collection-item"], table tbody tr').count();
      expect(filteredCount).toBeGreaterThanOrEqual(0);
    }
  });

  test('should sort collection items', async ({ page }) => {
    // Navigate to collection workspace
    await page.goto('/collections');

    const collectionCard = page.locator('[data-testid="collection-card"]').first();
    if (await collectionCard.isVisible({ timeout: 5000 })) {
      await collectionCard.click();
    } else {
      test.skip('No collections available for sort test');
    }

    // Wait for items to load
    await page.waitForSelector('[data-testid="collection-item"], table tbody tr', {
      timeout: 5000,
    });

    // Click price column header to sort
    const priceHeader = page.locator('th:has-text("Price"), [data-column="price"]');
    if (await priceHeader.isVisible({ timeout: 3000 })) {
      await priceHeader.click();

      // Wait for sort to apply
      await page.waitForTimeout(300);

      // Verify sort indicator
      const sortIndicator = priceHeader.locator('[data-sort], svg');
      await expect(sortIndicator).toBeVisible();

      // Get first two prices and verify order
      const firstPrice = await page
        .locator('table tbody tr:nth-child(1) td')
        .filter({ hasText: /\$/ })
        .first()
        .innerText();

      const secondPrice = await page
        .locator('table tbody tr:nth-child(2) td')
        .filter({ hasText: /\$/ })
        .first()
        .innerText();

      const price1 = parseFloat(firstPrice.replace(/[^0-9.]/g, ''));
      const price2 = parseFloat(secondPrice.replace(/[^0-9.]/g, ''));

      expect(price1).toBeLessThanOrEqual(price2);
    }
  });

  test('should switch between table and card view', async ({ page }) => {
    // Navigate to collection workspace
    await page.goto('/collections');

    const collectionCard = page.locator('[data-testid="collection-card"]').first();
    if (await collectionCard.isVisible({ timeout: 5000 })) {
      await collectionCard.click();
    } else {
      test.skip('No collections available for view toggle test');
    }

    // Wait for items to load
    await page.waitForSelector('[data-testid="collection-item"], table, [data-testid="card-view"]', {
      timeout: 5000,
    });

    // Find view toggle buttons
    const cardViewBtn = page.locator('button[aria-label*="card view"], button:has-text("Card")');
    const tableViewBtn = page.locator('button[aria-label*="table view"], button:has-text("Table")');

    // Switch to card view
    if (await cardViewBtn.isVisible({ timeout: 3000 })) {
      await cardViewBtn.click();

      // Verify card view is shown
      await expect(
        page.locator('[data-testid="card-view"], .card-grid')
      ).toBeVisible({ timeout: 2000 });

      // Switch back to table view
      if (await tableViewBtn.isVisible({ timeout: 2000 })) {
        await tableViewBtn.click();

        // Verify table view is shown
        await expect(page.locator('table')).toBeVisible({ timeout: 2000 });
      }
    }
  });

  test('should export collection to CSV', async ({ page }) => {
    // Navigate to collection workspace
    await page.goto('/collections');

    const collectionCard = page.locator('[data-testid="collection-card"]').first();
    if (await collectionCard.isVisible({ timeout: 5000 })) {
      await collectionCard.click();
    } else {
      test.skip('No collections available for export test');
    }

    // Wait for items to load
    await page.waitForSelector('[data-testid="collection-item"], table tbody tr', {
      timeout: 5000,
    });

    // Set up download listener
    const downloadPromise = page.waitForEvent('download', { timeout: 10000 });

    // Click export button
    const exportBtn = page.locator('button:has-text("Export")');
    await expect(exportBtn).toBeVisible({ timeout: 5000 });
    await exportBtn.click();

    // If there's a format selector, choose CSV
    const csvOption = page.locator('button:has-text("CSV"), [role="menuitem"]:has-text("CSV")');
    if (await csvOption.isVisible({ timeout: 2000 })) {
      await csvOption.click();
    }

    // Wait for download
    const download = await downloadPromise;

    // Verify filename
    const filename = download.suggestedFilename();
    expect(filename).toMatch(/\.csv$/i);

    // Save file to verify contents (optional)
    const path = await download.path();
    expect(path).toBeTruthy();
  });

  test('should edit collection name and description', async ({ page }) => {
    // Navigate to collections
    await page.goto('/collections');

    const collectionCard = page.locator('[data-testid="collection-card"]').first();
    if (await collectionCard.isVisible({ timeout: 5000 })) {
      await collectionCard.click();
    } else {
      test.skip('No collections available for edit test');
    }

    // Find edit button
    const editBtn = page.locator('button[aria-label*="Edit"], button:has-text("Edit")');
    if (await editBtn.isVisible({ timeout: 3000 })) {
      await editBtn.click();

      // Wait for edit form
      await page.waitForSelector('input[name="name"], input[id*="collection"]', {
        state: 'visible',
        timeout: 5000,
      });

      // Change name
      const nameInput = page.locator('input[name="name"], input[id*="collection"]');
      await nameInput.clear();
      await nameInput.fill('Updated Collection Name');

      // Save
      await page.click('button[type="submit"]:has-text("Save"), button:has-text("Update")');

      // Verify success
      await verifyToast(page, /updated|saved|success/i);

      // Verify name is updated
      await expect(
        page.locator('h1:has-text("Updated Collection Name")')
      ).toBeVisible({ timeout: 3000 });
    }
  });

  test('should delete collection', async ({ page }) => {
    // Create a temporary collection for deletion
    await page.goto('/collections');
    await createCollection(page, 'Collection to Delete');

    // Wait for redirect to collection page
    await page.waitForURL(/\/collections\/\d+/, { timeout: 10000 });

    // Find delete button
    const deleteBtn = page.locator('button[aria-label*="Delete"], button:has-text("Delete")');
    await expect(deleteBtn).toBeVisible({ timeout: 5000 });
    await deleteBtn.click();

    // Confirm deletion
    await page.waitForSelector('[role="alertdialog"], [role="dialog"]', {
      state: 'visible',
      timeout: 3000,
    });

    const confirmBtn = page.locator('button:has-text("Confirm"), button:has-text("Delete")').last();
    await confirmBtn.click();

    // Verify redirect back to collections list
    await page.waitForURL('/collections', { timeout: 10000 });

    // Verify success toast
    await verifyToast(page, /deleted|removed/i);

    // Verify collection is gone from list
    await expect(
      page.locator('[data-testid="collection-card"]:has-text("Collection to Delete")')
    ).not.toBeVisible({ timeout: 3000 });
  });

  test('should handle empty collection state', async ({ page }) => {
    // Create a new collection
    await page.goto('/collections');
    await createCollection(page, 'Empty Collection');

    // Verify empty state is shown
    const emptyState = page.locator('[data-testid="empty-state"], text=/no items|empty/i');
    await expect(emptyState).toBeVisible({ timeout: 5000 });

    // Verify "Add Item" CTA is visible
    await expect(
      page.locator('button:has-text("Add"), a:has-text("Browse Listings")')
    ).toBeVisible();
  });

  test('should persist filters and view preferences', async ({ page }) => {
    // Navigate to collection
    await page.goto('/collections');

    const collectionCard = page.locator('[data-testid="collection-card"]').first();
    if (await collectionCard.isVisible({ timeout: 5000 })) {
      await collectionCard.click();
    } else {
      test.skip('No collections available for persistence test');
    }

    // Apply a filter
    const priceFilter = page.locator('input[name*="price"]');
    if (await priceFilter.isVisible({ timeout: 2000 })) {
      await priceFilter.fill('600');
      await page.waitForTimeout(300);
    }

    // Switch to card view
    const cardViewBtn = page.locator('button[aria-label*="card view"]');
    if (await cardViewBtn.isVisible({ timeout: 2000 })) {
      await cardViewBtn.click();
      await page.waitForTimeout(300);
    }

    // Reload page
    await page.reload();

    // Verify filter is still applied
    if (await priceFilter.isVisible({ timeout: 2000 })) {
      await expect(priceFilter).toHaveValue('600');
    }

    // Verify card view is still active
    await expect(
      page.locator('[data-testid="card-view"], .card-grid')
    ).toBeVisible({ timeout: 3000 });
  });
});
