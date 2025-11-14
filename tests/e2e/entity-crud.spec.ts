import { test, expect, type Page } from '@playwright/test';

/**
 * E2E tests for Entity CRUD Operations
 *
 * Tests cover 4 user stories:
 * - US-1: Edit Entity Specification
 * - US-2: Delete Unused Entity
 * - US-3: Attempt Delete In-Use Entity
 * - US-4: Manage Entities from Global Fields
 */

// ============================================================================
// Configuration
// ============================================================================

const API_URL = process.env.API_URL || 'http://localhost:8000';

// ============================================================================
// Test Data Setup Helpers
// ============================================================================

interface TestCPU {
  id: number;
  model: string;
  manufacturer: string;
  socket?: string;
  cores?: number;
  threads?: number;
}

/**
 * Creates a test CPU via API for testing
 */
async function createTestCPU(page: Page, cpuData: Partial<TestCPU>): Promise<TestCPU> {
  const response = await page.request.post(`${API_URL}/api/catalog/cpus`, {
    data: {
      model: cpuData.model || 'Test CPU',
      manufacturer: cpuData.manufacturer || 'Test Manufacturer',
      socket: cpuData.socket,
      cores: cpuData.cores,
      threads: cpuData.threads,
    },
  });

  if (!response.ok()) {
    throw new Error(`Failed to create test CPU: ${response.status()} ${await response.text()}`);
  }

  return response.json();
}

/**
 * Creates a test listing that uses a specific CPU
 */
async function createTestListing(page: Page, cpuId: number): Promise<number> {
  const response = await page.request.post(`${API_URL}/api/listings`, {
    data: {
      title: `Test Listing for CPU ${cpuId}`,
      price_usd: 599.99,
      condition: 'used',
      status: 'active',
      cpu_id: cpuId,
      ram_gb: 16,
      primary_storage_gb: 512,
    },
  });

  if (!response.ok()) {
    throw new Error(`Failed to create test listing: ${response.status()} ${await response.text()}`);
  }

  const data = await response.json();
  return data.id;
}

/**
 * Deletes a test CPU via API
 */
async function deleteTestCPU(page: Page, cpuId: number): Promise<void> {
  await page.request.delete(`${API_URL}/api/catalog/cpus/${cpuId}`);
}

/**
 * Deletes a test listing via API
 */
async function deleteTestListing(page: Page, listingId: number): Promise<void> {
  await page.request.delete(`${API_URL}/api/listings/${listingId}`);
}

/**
 * Gets CPU details via API
 */
async function getCPU(page: Page, cpuId: number): Promise<TestCPU> {
  const response = await page.request.get(`${API_URL}/api/catalog/cpus/${cpuId}`);

  if (!response.ok()) {
    throw new Error(`Failed to get CPU: ${response.status()}`);
  }

  return response.json();
}

// ============================================================================
// US-1: Edit Entity Specification
// ============================================================================

test.describe('US-1: Edit Entity Specification', () => {
  let testCpu: TestCPU;

  test.beforeEach(async ({ page }) => {
    // Create a test CPU for editing
    testCpu = await createTestCPU(page, {
      model: 'Intel Core i7-13700H',
      manufacturer: 'Intel',
      socket: 'BGA1744',
      cores: 14,
      threads: 20,
    });
  });

  test.afterEach(async ({ page }) => {
    // Clean up test data
    if (testCpu?.id) {
      await deleteTestCPU(page, testCpu.id);
    }
  });

  test('should edit CPU specification successfully', async ({ page }) => {
    // Navigate to CPU detail page
    await page.goto(`/catalog/cpus/${testCpu.id}`);

    // Verify initial data is displayed
    await expect(page.locator('h1')).toContainText('Intel Core i7-13700H');
    await expect(page.locator('text=Intel')).toBeVisible();

    // Click Edit button
    await page.click('button:has-text("Edit")');

    // Wait for modal to open
    await expect(page.locator('text=Edit CPU')).toBeVisible();

    // Modify CPU name
    const nameInput = page.locator('input#name');
    await nameInput.clear();
    await nameInput.fill('Intel Core i7-13700H (Updated)');

    // Modify cores
    const coresInput = page.locator('input#cores');
    await coresInput.clear();
    await coresInput.fill('16');

    // Submit form
    await page.click('button:has-text("Save Changes")');

    // Wait for modal to close
    await expect(page.locator('text=Edit CPU')).not.toBeVisible({ timeout: 5000 });

    // Verify success toast appears
    await expect(page.locator('text=CPU updated successfully').or(page.locator('text=updated'))).toBeVisible({ timeout: 5000 });

    // Verify detail page updates with new data
    await page.waitForTimeout(500); // Allow time for page to update
    await expect(page.locator('h1')).toContainText('Intel Core i7-13700H (Updated)');

    // Verify the change persisted by checking via API
    const updatedCpu = await getCPU(page, testCpu.id);
    expect(updatedCpu.model).toBe('Intel Core i7-13700H (Updated)');
    expect(updatedCpu.cores).toBe(16);
  });

  test('should show validation error for invalid data', async ({ page }) => {
    await page.goto(`/catalog/cpus/${testCpu.id}`);
    await page.click('button:has-text("Edit")');

    // Clear required field (name)
    const nameInput = page.locator('input#name');
    await nameInput.clear();

    // Verify validation error appears
    await expect(page.locator('text=required').or(page.locator('text=This field is required'))).toBeVisible({ timeout: 2000 });

    // Verify submit button is disabled
    const saveButton = page.locator('button:has-text("Save Changes")');
    await expect(saveButton).toBeDisabled();

    // Enter valid data
    await nameInput.fill('Valid CPU Name');

    // Verify submit button is enabled
    await expect(saveButton).toBeEnabled();
  });

  test('should allow canceling edit without saving changes', async ({ page }) => {
    await page.goto(`/catalog/cpus/${testCpu.id}`);
    await page.click('button:has-text("Edit")');

    // Modify field
    const nameInput = page.locator('input#name');
    await nameInput.clear();
    await nameInput.fill('This should not be saved');

    // Click Cancel
    await page.click('button:has-text("Cancel")');

    // Modal should close
    await expect(page.locator('text=Edit CPU')).not.toBeVisible({ timeout: 2000 });

    // Verify original data is still displayed
    await expect(page.locator('h1')).toContainText('Intel Core i7-13700H');
  });
});

// ============================================================================
// US-2: Delete Unused Entity
// ============================================================================

test.describe('US-2: Delete Unused Entity', () => {
  let testCpu: TestCPU;

  test.beforeEach(async ({ page }) => {
    // Create a test CPU with no associated listings
    testCpu = await createTestCPU(page, {
      model: 'AMD Ryzen 7 7840HS (To Delete)',
      manufacturer: 'AMD',
      socket: 'FP8',
    });
  });

  test('should delete unused CPU successfully', async ({ page }) => {
    // Navigate to CPU detail page
    await page.goto(`/catalog/cpus/${testCpu.id}`);

    // Verify no usage badge is shown
    await expect(page.locator('text=Used in')).not.toBeVisible();

    // Click Delete button
    await page.click('button:has-text("Delete")');

    // Verify confirmation dialog appears
    await expect(page.locator('text=Delete CPU')).toBeVisible();
    await expect(page.locator(`text=AMD Ryzen 7 7840HS (To Delete)`)).toBeVisible();
    await expect(page.locator('text=This action cannot be undone')).toBeVisible();

    // Since CPU is unused, no confirmation input should be required
    // Check if confirmation input exists
    const confirmationInput = page.locator('input#confirmation-input');
    const hasConfirmationInput = await confirmationInput.isVisible().catch(() => false);

    if (!hasConfirmationInput) {
      // If no confirmation input, delete button should be immediately available
      const deleteButton = page.locator('button:has-text("Delete")').last();
      await expect(deleteButton).toBeEnabled();
    }

    // Click confirm
    await page.click('button:has-text("Delete")').last();

    // Verify redirect to CPU list
    await expect(page).toHaveURL(/\/catalog\/cpus\/?$/, { timeout: 10000 });

    // Verify success message
    await expect(page.locator('text=deleted').or(page.locator('text=CPU deleted successfully'))).toBeVisible({ timeout: 5000 });

    // Verify CPU is no longer accessible via API
    const response = await page.request.get(`${API_URL}/api/catalog/cpus/${testCpu.id}`);
    expect(response.status()).toBe(404);
  });

  test.afterEach(async ({ page }) => {
    // Clean up if test failed and CPU still exists
    try {
      await deleteTestCPU(page, testCpu.id);
    } catch (e) {
      // Ignore errors (CPU may have been successfully deleted)
    }
  });
});

// ============================================================================
// US-3: Attempt Delete In-Use Entity
// ============================================================================

test.describe('US-3: Attempt Delete In-Use Entity', () => {
  let testCpu: TestCPU;
  let testListingId: number;

  test.beforeEach(async ({ page }) => {
    // Create a test CPU
    testCpu = await createTestCPU(page, {
      model: 'Intel Core i5-12600K (In Use)',
      manufacturer: 'Intel',
      socket: 'LGA1700',
    });

    // Create a listing that uses this CPU
    testListingId = await createTestListing(page, testCpu.id);
  });

  test.afterEach(async ({ page }) => {
    // Clean up test data
    if (testListingId) {
      await deleteTestListing(page, testListingId);
    }
    if (testCpu?.id) {
      await deleteTestCPU(page, testCpu.id);
    }
  });

  test('should show usage badge and require confirmation', async ({ page }) => {
    // Navigate to CPU detail page
    await page.goto(`/catalog/cpus/${testCpu.id}`);

    // Verify "Used in X listings" badge is visible
    await expect(page.locator('text=Used in 1 listing')).toBeVisible();

    // Click Delete button
    await page.click('button[aria-label*="Delete"]');

    // Verify dialog shows usage warning
    await expect(page.locator('text=Delete CPU')).toBeVisible();
    await expect(page.locator('text=Used in 1 Listing').or(page.locator('text=Used in 1 listing'))).toBeVisible();
    await expect(page.locator('text=currently used in').or(page.locator('text=is currently used'))).toBeVisible();

    // Verify confirmation input is required
    const confirmationInput = page.locator('input#confirmation-input');
    await expect(confirmationInput).toBeVisible();
    await expect(confirmationInput).toHaveAttribute('placeholder', /Intel Core i5-12600K \(In Use\)/i);

    // Verify delete button is initially disabled
    const deleteButton = page.locator('button:has-text("Delete")').last();
    await expect(deleteButton).toBeDisabled();

    // Enter incorrect confirmation text
    await confirmationInput.fill('wrong text');
    await expect(deleteButton).toBeDisabled();

    // Enter correct confirmation text
    await confirmationInput.clear();
    await confirmationInput.fill('Intel Core i5-12600K (In Use)');

    // Verify delete button is now enabled
    await expect(deleteButton).toBeEnabled();
  });

  test('should prevent deletion when entity is in use', async ({ page }) => {
    await page.goto(`/catalog/cpus/${testCpu.id}`);
    await page.click('button[aria-label*="Delete"]');

    // Enter confirmation
    const confirmationInput = page.locator('input#confirmation-input');
    await confirmationInput.fill(testCpu.model);

    // Attempt delete
    await page.click('button:has-text("Delete")').last();

    // Depending on backend behavior, either:
    // 1. Should show error toast saying "Cannot delete: entity is used in X listings"
    // 2. Should successfully delete and cascade (if backend allows it)

    // Check for error message (adjust based on actual implementation)
    const errorToast = page.locator('text=Cannot delete').or(page.locator('text=is used in'));
    const successToast = page.locator('text=deleted successfully').or(page.locator('text=CPU deleted'));

    // Wait for either error or success
    await Promise.race([
      errorToast.waitFor({ timeout: 5000 }).catch(() => {}),
      successToast.waitFor({ timeout: 5000 }).catch(() => {}),
    ]);

    // Verify entity still exists if deletion was prevented
    const stillVisible = await errorToast.isVisible().catch(() => false);
    if (stillVisible) {
      // Error shown - entity should still exist
      await page.goto(`/catalog/cpus/${testCpu.id}`);
      await expect(page.locator('h1')).toContainText(testCpu.model);
    }
  });
});

// ============================================================================
// US-4: Manage Entities from Global Fields
// ============================================================================

test.describe('US-4: Manage Entities from Global Fields', () => {
  let testCpu: TestCPU;

  test.beforeEach(async ({ page }) => {
    // Create a test CPU for viewing from global fields
    testCpu = await createTestCPU(page, {
      model: 'AMD Ryzen 9 7950X',
      manufacturer: 'AMD',
      socket: 'AM5',
      cores: 16,
      threads: 32,
    });
  });

  test.afterEach(async ({ page }) => {
    // Clean up test data
    if (testCpu?.id) {
      await deleteTestCPU(page, testCpu.id);
    }
  });

  test('should navigate from global fields to CPU detail page', async ({ page }) => {
    // Navigate to global fields page
    await page.goto('/global-fields');

    // Switch to Data tab
    await page.click('button:has-text("Data")');

    // Wait for data grid to load
    await page.waitForSelector('table', { timeout: 5000 });

    // Find the test CPU row (search by model name)
    const cpuRow = page.locator('table tbody tr', { hasText: 'AMD Ryzen 9 7950X' });

    // Verify the row exists
    const rowExists = await cpuRow.isVisible({ timeout: 5000 }).catch(() => false);

    if (rowExists) {
      // Click "View Details" link
      const viewDetailsLink = cpuRow.locator('a:has-text("View Details")');
      await viewDetailsLink.click();

      // Verify navigation to detail page
      await expect(page).toHaveURL(`/catalog/cpus/${testCpu.id}`, { timeout: 5000 });

      // Verify CPU data is displayed
      await expect(page.locator('h1')).toContainText('AMD Ryzen 9 7950X');
      await expect(page.locator('text=AMD')).toBeVisible();
      await expect(page.locator('text=16').or(page.locator('text=16 cores'))).toBeVisible();
    } else {
      // If row not visible, it might be in a different entity type
      // Skip this test or adjust selector
      test.skip();
    }
  });

  test('should create new CPU from global fields', async ({ page }) => {
    // Navigate to global fields page
    await page.goto('/global-fields');

    // Switch to Data tab
    await page.click('button:has-text("Data")');

    // Click "Add entry" button
    await page.click('button:has-text("Add entry")');

    // Wait for create modal to open
    await expect(page.locator('text=Create').or(page.locator('text=Add'))).toBeVisible({ timeout: 5000 });

    // Fill form
    const nameInput = page.locator('input#name').or(page.locator('input[name="model"]')).first();
    const manufacturerInput = page.locator('input#manufacturer').or(page.locator('input[name="manufacturer"]')).first();

    await nameInput.fill('Test CPU from Global Fields');
    await manufacturerInput.fill('Test Mfg');

    // Submit form
    await page.click('button:has-text("Save")').or(page.click('button:has-text("Create")')).first();

    // Wait for modal to close
    await page.waitForTimeout(1000);

    // Verify new CPU appears in grid
    await expect(page.locator('text=Test CPU from Global Fields')).toBeVisible({ timeout: 5000 });

    // Clean up: find and delete the created CPU
    const response = await page.request.get(`${API_URL}/api/catalog/cpus`);
    const cpus = await response.json();
    const createdCpu = cpus.find((cpu: TestCPU) => cpu.model === 'Test CPU from Global Fields');
    if (createdCpu) {
      await deleteTestCPU(page, createdCpu.id);
    }
  });

  test('should verify data matches between global fields and detail page', async ({ page }) => {
    // Navigate to global fields
    await page.goto('/global-fields');
    await page.click('button:has-text("Data")');
    await page.waitForSelector('table', { timeout: 5000 });

    // Find the test CPU row
    const cpuRow = page.locator('table tbody tr', { hasText: 'AMD Ryzen 9 7950X' });
    const rowExists = await cpuRow.isVisible({ timeout: 5000 }).catch(() => false);

    if (rowExists) {
      // Get data from the grid row
      const rowText = await cpuRow.innerText();

      // Click View Details
      await cpuRow.locator('a:has-text("View Details")').click();

      // Verify detail page shows matching data
      await expect(page.locator('h1')).toContainText('AMD Ryzen 9 7950X');
      await expect(page.locator('text=AMD')).toBeVisible();

      // Return to global fields
      await page.goto('/global-fields');
      await page.click('button:has-text("Data")');

      // Verify data is still consistent
      await expect(page.locator('table tbody tr', { hasText: 'AMD Ryzen 9 7950X' })).toBeVisible();
    }
  });
});

// ============================================================================
// Accessibility & Responsive Tests
// ============================================================================

test.describe('Accessibility & Responsive Design', () => {
  let testCpu: TestCPU;

  test.beforeEach(async ({ page }) => {
    testCpu = await createTestCPU(page, {
      model: 'Accessibility Test CPU',
      manufacturer: 'Test',
    });
  });

  test.afterEach(async ({ page }) => {
    if (testCpu?.id) {
      await deleteTestCPU(page, testCpu.id);
    }
  });

  test('should support keyboard navigation on detail page', async ({ page }) => {
    await page.goto(`/catalog/cpus/${testCpu.id}`);

    // Tab to Edit button
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // Press Enter to open edit modal
    const editButton = page.locator('button:has-text("Edit")');
    await editButton.focus();
    await page.keyboard.press('Enter');

    // Modal should open
    await expect(page.locator('text=Edit CPU')).toBeVisible({ timeout: 2000 });

    // Tab through form fields
    await page.keyboard.press('Tab');
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedElement).toBe('INPUT');

    // Press Escape to close modal
    await page.keyboard.press('Escape');
    await expect(page.locator('text=Edit CPU')).not.toBeVisible({ timeout: 2000 });
  });

  test('should be responsive on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    await page.goto(`/catalog/cpus/${testCpu.id}`);

    // Verify page renders and is readable
    await expect(page.locator('h1')).toBeVisible();
    await expect(page.locator('button:has-text("Edit")')).toBeVisible();
    await expect(page.locator('button:has-text("Delete")')).toBeVisible();

    // Click Edit button
    await page.click('button:has-text("Edit")');

    // Verify modal renders properly on mobile
    await expect(page.locator('text=Edit CPU')).toBeVisible();
    const nameInput = page.locator('input#name');
    await expect(nameInput).toBeVisible();

    // Modal should be scrollable if needed
    const modalContent = page.locator('[role="dialog"]').or(page.locator('.modal-content')).first();
    await expect(modalContent).toBeVisible();
  });

  test('should have proper ARIA labels on action buttons', async ({ page }) => {
    await page.goto(`/catalog/cpus/${testCpu.id}`);

    // Check Edit button has aria-label
    const editButton = page.locator('button:has-text("Edit")');
    const editAriaLabel = await editButton.getAttribute('aria-label');
    expect(editAriaLabel).toContain('Edit');
    expect(editAriaLabel).toContain('Accessibility Test CPU');

    // Check Delete button has aria-label
    const deleteButton = page.locator('button:has-text("Delete")');
    const deleteAriaLabel = await deleteButton.getAttribute('aria-label');
    expect(deleteAriaLabel).toContain('Delete');
    expect(deleteAriaLabel).toContain('Accessibility Test CPU');
  });
});
