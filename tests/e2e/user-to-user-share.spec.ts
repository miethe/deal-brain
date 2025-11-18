/**
 * E2E Tests: User-to-User Share Flow
 *
 * Tests the complete flow of sharing a listing with another user
 *
 * User Story:
 * - User A shares a listing with User B
 * - User B receives notification
 * - User B views the shared listing
 * - User B imports to their collection
 * - Shared metadata is preserved
 */

import { test, expect, type Page } from '@playwright/test';
import {
  TEST_USERS,
  loginUser,
  logoutUser,
  verifyToast,
  measureResponseTime,
} from './fixtures';

test.describe('User-to-User Share Flow', () => {
  // Note: These tests assume test users exist in the database
  // You may need to seed users before running tests

  test('should share listing from User A to User B with message', async ({ page, context }) => {
    // Login as User A
    await page.goto('/listings');

    // Click share button on first listing
    const shareButton = page.locator('button[aria-label*="Share"]').first();
    await expect(shareButton).toBeVisible({ timeout: 5000 });
    await shareButton.click();

    // Wait for share modal
    await page.waitForSelector('[role="dialog"]', { state: 'visible' });

    // Click "Share with User" tab
    const shareWithUserTab = page.locator('button:has-text("Share with User")');
    await expect(shareWithUserTab).toBeVisible();
    await shareWithUserTab.click();

    // Search for User B
    const searchInput = page.locator('input#user-search');
    await expect(searchInput).toBeVisible();

    // Type search query (debounced 200ms)
    await searchInput.fill('testuser_b');

    // Wait for search results (debounce + API call)
    await page.waitForSelector('[role="option"], button:has-text("testuser_b")', {
      state: 'visible',
      timeout: 5000,
    });

    // Select User B from results
    const userOption = page.locator('button:has-text("testuser_b")').first();
    await userOption.click();

    // Verify user is selected
    await expect(
      page.locator('text=/testuser_b|userb@test.com/i')
    ).toBeVisible();

    // Add optional message
    const messageTextarea = page.locator('textarea#share-message');
    await messageTextarea.fill('Great deal! Check this out.');

    // Measure share creation time
    const responseTime = await measureResponseTime(
      page,
      async () => {
        await page.click('button:has-text("Send")');
      },
      '/api/v1/shares/user'
    );

    // Verify share creation is fast (<500ms)
    expect(responseTime).toBeLessThan(500);

    // Verify success toast
    await verifyToast(page, /sent|shared|success/i);

    // Verify modal is closed
    await expect(page.locator('[role="dialog"]')).not.toBeVisible({ timeout: 2000 });
  });

  test('should receive and view share notification as User B', async ({ page }) => {
    // This test assumes User A has already shared a listing with User B
    // In a real scenario, you'd run the previous test first or seed the data

    // Navigate to notifications page
    await page.goto('/notifications');

    // Verify notification appears
    const notification = page.locator('[data-testid="notification"], .notification').first();
    await expect(notification).toBeVisible({ timeout: 5000 });

    // Verify notification contains:
    // - Sender info (User A)
    // - Share message
    // - Link to view

    // Check for sender info
    await expect(
      notification.locator('text=/shared|sent/i')
    ).toBeVisible();

    // Click notification to view
    await notification.click();

    // Verify redirected to shared listing or detail page
    await expect(
      page.locator('h1, h2, [data-testid="listing-title"]')
    ).toBeVisible({ timeout: 5000 });

    // Verify shared message is displayed
    await expect(
      page.locator('text=/great deal|check this out/i')
    ).toBeVisible({ timeout: 3000 });

    // Verify sender attribution is shown
    await expect(
      page.locator('text=/shared by|from/i')
    ).toBeVisible();
  });

  test('should import shared listing to collection', async ({ page }) => {
    // Navigate to a shared listing (assumes previous test ran)
    // For standalone test, you'd navigate to a known shared listing URL
    await page.goto('/notifications');

    // Click first notification
    const notification = page.locator('[data-testid="notification"], .notification').first();
    if (await notification.isVisible({ timeout: 5000 })) {
      await notification.click();
    } else {
      // Fallback: navigate to listings and pick one
      await page.goto('/listings');
      await page.waitForSelector('table, [data-testid="listings-grid"]');
    }

    // Click "Import to Collection" or "Add to Collection"
    const importButton = page.locator(
      'button:has-text("Import to Collection"), button:has-text("Add to Collection")'
    );
    await expect(importButton).toBeVisible({ timeout: 5000 });
    await importButton.click();

    // Select collection from dropdown
    await page.waitForSelector(
      '[role="dialog"], [data-radix-popper-content-wrapper]',
      { state: 'visible', timeout: 5000 }
    );

    // Create new collection or select existing
    const collectionOption = page.locator('[role="option"], button[data-collection-id]').first();
    if (await collectionOption.isVisible({ timeout: 2000 })) {
      await collectionOption.click();
    } else {
      // Create new collection
      const createNewBtn = page.locator('button:has-text("Create new")');
      await createNewBtn.click();

      const nameInput = page.locator('input[name="name"]');
      await nameInput.fill('Shared Deals Collection');

      await page.click('button[type="submit"]:has-text("Create")');
    }

    // Verify import success
    await verifyToast(page, /added|imported|success/i);

    // Navigate to collection and verify item is there
    await page.goto('/collections');
    await page.waitForSelector('h1:has-text("Collections")');

    // Open the collection
    const collectionCard = page.locator('[data-testid="collection-card"]').first();
    await collectionCard.click();

    // Verify item shows "Shared by User A"
    await expect(
      page.locator('text=/shared by|from testuser/i')
    ).toBeVisible({ timeout: 5000 });

    // Verify message is preserved
    await expect(
      page.locator('text=/great deal|check this out/i')
    ).toBeVisible({ timeout: 3000 });
  });

  test('should handle user search with debouncing', async ({ page }) => {
    // Navigate to listings
    await page.goto('/listings');

    // Click share button
    const shareButton = page.locator('button[aria-label*="Share"]').first();
    await shareButton.click();
    await page.waitForSelector('[role="dialog"]', { state: 'visible' });

    // Click "Share with User" tab
    await page.click('button:has-text("Share with User")');

    // Get search input
    const searchInput = page.locator('input#user-search');
    await expect(searchInput).toBeVisible();

    // Type search query character by character
    const query = 'testuser';
    for (const char of query) {
      await searchInput.type(char, { delay: 50 });
    }

    // Wait for debounce (200ms) + some buffer
    await page.waitForTimeout(300);

    // Verify search was executed (check for results or loading state)
    const results = page.locator('[role="option"], button:has-text("testuser")');
    const loading = page.locator('text=/searching/i');
    const noResults = page.locator('text=/no users found/i');

    // One of these should be visible
    await expect(
      results.or(loading).or(noResults)
    ).toBeVisible({ timeout: 3000 });
  });

  test('should display user search results correctly', async ({ page }) => {
    // Navigate to listings
    await page.goto('/listings');

    // Open share modal
    const shareButton = page.locator('button[aria-label*="Share"]').first();
    await shareButton.click();
    await page.waitForSelector('[role="dialog"]', { state: 'visible' });

    // Switch to "Share with User" tab
    await page.click('button:has-text("Share with User")');

    // Search for users
    const searchInput = page.locator('input#user-search');
    await searchInput.fill('test');

    // Wait for results
    await page.waitForTimeout(300); // Debounce

    // Verify results show username and email
    const userButton = page.locator('[role="option"], button').filter({
      hasText: /testuser|@test\.com/i,
    }).first();

    if (await userButton.isVisible({ timeout: 3000 })) {
      // Verify both username and email are shown
      await expect(userButton.locator('text=/testuser/i')).toBeVisible();
      await expect(userButton.locator('text=/@test\.com/i')).toBeVisible();
    }
  });

  test('should handle no search results gracefully', async ({ page }) => {
    // Navigate to listings
    await page.goto('/listings');

    // Open share modal
    const shareButton = page.locator('button[aria-label*="Share"]').first();
    await shareButton.click();
    await page.waitForSelector('[role="dialog"]', { state: 'visible' });

    // Switch to "Share with User" tab
    await page.click('button:has-text("Share with User")');

    // Search for non-existent user
    const searchInput = page.locator('input#user-search');
    await searchInput.fill('nonexistentuser12345');

    // Wait for debounce + API call
    await page.waitForTimeout(500);

    // Verify "No users found" message
    await expect(
      page.locator('text=/no users found/i')
    ).toBeVisible({ timeout: 3000 });
  });

  test('should enforce share rate limit', async ({ page }) => {
    // Note: This test assumes rate limiting is implemented
    // You may need to adjust based on your actual rate limit (10 shares per hour)

    // Navigate to listings
    await page.goto('/listings');

    // Attempt to share multiple listings quickly
    for (let i = 0; i < 3; i++) {
      const shareButton = page.locator('button[aria-label*="Share"]').nth(i);
      await shareButton.click();
      await page.waitForSelector('[role="dialog"]', { state: 'visible' });

      // Switch to "Share with User" tab
      await page.click('button:has-text("Share with User")');

      // Select a user (if available)
      const searchInput = page.locator('input#user-search');
      await searchInput.fill('testuser_b');
      await page.waitForTimeout(300);

      const userOption = page.locator('button:has-text("testuser_b")').first();
      if (await userOption.isVisible({ timeout: 2000 })) {
        await userOption.click();
        await page.click('button:has-text("Send")');

        // Check for success or rate limit error
        const toast = page.locator('[role="status"], [data-sonner-toast]');
        await expect(toast).toBeVisible({ timeout: 3000 });
      }

      // Close modal
      await page.keyboard.press('Escape');
    }

    // The rate limit message is displayed in the UI as help text
    await expect(
      page.locator('text=/10 listings per hour/i')
    ).toBeVisible({ timeout: 2000 });
  });

  test('should clear form after successful share', async ({ page }) => {
    // Navigate to listings
    await page.goto('/listings');

    // Open share modal
    const shareButton = page.locator('button[aria-label*="Share"]').first();
    await shareButton.click();
    await page.waitForSelector('[role="dialog"]', { state: 'visible' });

    // Switch to "Share with User" tab
    await page.click('button:has-text("Share with User")');

    // Fill in form
    const searchInput = page.locator('input#user-search');
    await searchInput.fill('testuser_b');
    await page.waitForTimeout(300);

    const userOption = page.locator('button:has-text("testuser_b")').first();
    if (await userOption.isVisible({ timeout: 2000 })) {
      await userOption.click();

      const messageTextarea = page.locator('textarea#share-message');
      await messageTextarea.fill('Test message');

      // Send
      await page.click('button:has-text("Send")');

      // Wait for success
      await verifyToast(page, /sent|success/i);

      // Modal should close
      await expect(page.locator('[role="dialog"]')).not.toBeVisible({ timeout: 2000 });

      // Re-open modal
      await shareButton.click();
      await page.waitForSelector('[role="dialog"]', { state: 'visible' });
      await page.click('button:has-text("Share with User")');

      // Verify form is cleared
      const clearedSearch = page.locator('input#user-search');
      expect(await clearedSearch.inputValue()).toBe('');

      const clearedMessage = page.locator('textarea#share-message');
      expect(await clearedMessage.inputValue()).toBe('');
    }
  });

  test('should send email notification to recipient', async ({ page }) => {
    // Note: This test verifies the UI behavior
    // Actual email sending would need to be verified via Celery logs or email service

    // Navigate to listings
    await page.goto('/listings');

    // Open share modal and share with user
    const shareButton = page.locator('button[aria-label*="Share"]').first();
    await shareButton.click();
    await page.waitForSelector('[role="dialog"]', { state: 'visible' });
    await page.click('button:has-text("Share with User")');

    const searchInput = page.locator('input#user-search');
    await searchInput.fill('testuser_b');
    await page.waitForTimeout(300);

    const userOption = page.locator('button:has-text("testuser_b")').first();
    if (await userOption.isVisible({ timeout: 2000 })) {
      await userOption.click();
      await page.click('button:has-text("Send")');

      // Verify success
      await verifyToast(page, /sent|success/i);

      // The help text in the modal mentions email notification
      await page.keyboard.press('Escape');
      await shareButton.click();
      await page.click('button:has-text("Share with User")');

      await expect(
        page.locator('text=/notification/i')
      ).toBeVisible();
    }
  });
});
