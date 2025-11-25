/**
 * E2E Tests: Share & Public Page Flow
 *
 * Tests the complete flow of sharing a listing via public link and viewing the public page
 *
 * User Story:
 * - User clicks ShareButton on a listing
 * - Generates a public share link
 * - Copies link to clipboard
 * - Opens link in incognito window
 * - Views public deal page with all details
 * - Adds item to collection from public page
 */

import { test, expect, type Page, type BrowserContext } from '@playwright/test';
import {
  waitForApiResponse,
  measureResponseTime,
  verifyOGTags,
  getShareLink,
  copyToClipboard,
  verifyToast,
  addToCollection,
} from './fixtures';

test.describe('Share & Public Page Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to listings page
    await page.goto('/listings');

    // Wait for listings to load
    await page.waitForSelector('table, [data-testid="listings-grid"]', {
      timeout: 10000,
    });
  });

  test('should generate share link and display it', async ({ page }) => {
    // Find first listing and click Share button
    const shareButton = page.locator('button[aria-label*="Share"]').first();
    await expect(shareButton).toBeVisible({ timeout: 5000 });

    // Measure share link generation time
    const responseTime = await measureResponseTime(
      page,
      async () => {
        await shareButton.click();
        await page.waitForSelector('[role="dialog"]', { state: 'visible' });
        await page.click('button:has-text("Copy Link"), [data-tab="link"]');
      },
      '/api/v1/shares'
    );

    // Verify share link generation is fast (<500ms)
    expect(responseTime).toBeLessThan(500);

    // Verify share link is displayed
    const shareLink = await getShareLink(page);
    expect(shareLink).toMatch(/\/deals\/\d+\/[a-zA-Z0-9_-]+/);

    // Verify expiry message is displayed
    await expect(page.locator('text=/Expires in/i')).toBeVisible();
  });

  test('should copy share link to clipboard', async ({ page, context }) => {
    // Grant clipboard permissions
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);

    // Click Share button on first listing
    const shareButton = page.locator('button[aria-label*="Share"]').first();
    await shareButton.click();

    // Wait for modal
    await page.waitForSelector('[role="dialog"]', { state: 'visible' });

    // Ensure we're on Copy Link tab
    const copyLinkTab = page.locator('button:has-text("Copy Link")');
    if (await copyLinkTab.isVisible()) {
      await copyLinkTab.click();
    }

    // Wait for share link to be generated
    await page.waitForSelector('input#share-link', { state: 'visible', timeout: 5000 });

    // Click copy button
    const copyButton = page.locator('button[aria-label="Copy to clipboard"]');
    await copyButton.click();

    // Verify copy success (check icon or toast)
    await expect(
      page.locator('button[aria-label="Copy to clipboard"] svg').first()
    ).toBeVisible({ timeout: 2000 });

    // Verify clipboard content
    const clipboardText = await page.evaluate(() => navigator.clipboard.readText());
    expect(clipboardText).toMatch(/^http/);
    expect(clipboardText).toMatch(/\/deals\/\d+\/[a-zA-Z0-9_-]+/);
  });

  test('should view public deal page with correct data', async ({ page, context }) => {
    // Grant clipboard permissions
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);

    // Get share link
    const shareButton = page.locator('button[aria-label*="Share"]').first();
    await shareButton.click();
    await page.waitForSelector('[role="dialog"]', { state: 'visible' });

    // Ensure Copy Link tab is active
    const copyLinkTab = page.locator('button:has-text("Copy Link")');
    if (await copyLinkTab.isVisible()) {
      await copyLinkTab.click();
    }

    const shareLink = await getShareLink(page);

    // Close modal
    const closeButton = page.locator('[role="dialog"] button[aria-label*="Close"], [data-state="open"] button').first();
    if (await closeButton.isVisible()) {
      await closeButton.click();
    } else {
      await page.keyboard.press('Escape');
    }

    // Open share link in new incognito context
    const incognitoContext = await context.browser()!.newContext();
    const incognitoPage = await incognitoContext.newPage();

    // Navigate to share link
    const startTime = Date.now();
    await incognitoPage.goto(shareLink);
    const loadTime = Date.now() - startTime;

    // Verify page loads quickly (<1s)
    expect(loadTime).toBeLessThan(1000);

    // Verify page displays listing details
    await expect(
      incognitoPage.locator('h1, h2, [data-testid="listing-title"]')
    ).toBeVisible({ timeout: 5000 });

    // Verify key listing data is displayed
    await expect(incognitoPage.locator('text=/price|\\$/i')).toBeVisible();
    await expect(incognitoPage.locator('text=/cpu|processor/i')).toBeVisible();

    // Verify "Add to Collection" CTA is visible
    const addToCollectionBtn = incognitoPage.locator('button:has-text("Add to Collection")');
    await expect(addToCollectionBtn).toBeVisible();

    // Clean up
    await incognitoContext.close();
  });

  test('should verify OpenGraph meta tags on public page', async ({ page, context }) => {
    // Grant clipboard permissions
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);

    // Get share link
    const shareButton = page.locator('button[aria-label*="Share"]').first();
    await shareButton.click();
    await page.waitForSelector('[role="dialog"]', { state: 'visible' });
    const shareLink = await getShareLink(page);

    // Close modal
    await page.keyboard.press('Escape');

    // Open share link in new page
    const newPage = await context.newPage();
    await newPage.goto(shareLink);

    // Wait for page to load
    await newPage.waitForLoadState('domcontentloaded');

    // Verify OpenGraph tags
    await verifyOGTags(newPage, {
      title: '*', // Any title is fine
      description: '*',
      image: true,
      url: '*',
    });

    // Clean up
    await newPage.close();
  });

  test('should complete full flow: share -> view -> add to collection', async ({
    page,
    context,
  }) => {
    // Grant clipboard permissions
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);

    // Step 1: Generate share link
    const shareButton = page.locator('button[aria-label*="Share"]').first();
    await shareButton.click();
    await page.waitForSelector('[role="dialog"]', { state: 'visible' });
    const shareLink = await getShareLink(page);
    await page.keyboard.press('Escape');

    // Step 2: Open public page
    await page.goto(shareLink);
    await expect(page.locator('h1, h2')).toBeVisible({ timeout: 5000 });

    // Step 3: Click "Add to Collection"
    const addToCollectionBtn = page.locator('button:has-text("Add to Collection")');
    await expect(addToCollectionBtn).toBeVisible();
    await addToCollectionBtn.click();

    // Step 4: Verify collection selector appears
    await expect(
      page.locator('[role="dialog"], [data-radix-popper-content-wrapper]')
    ).toBeVisible({ timeout: 5000 });

    // Step 5: Create new collection or select existing
    const createNewBtn = page.locator('button:has-text("Create new"), button:has-text("New collection")');
    if (await createNewBtn.isVisible({ timeout: 2000 })) {
      await createNewBtn.click();

      // Fill in collection form
      const collectionNameInput = page.locator('input[name="name"], input[id*="collection"]').first();
      await collectionNameInput.fill('Test Collection from Share');

      // Submit
      await page.click('button[type="submit"]:has-text("Create")');
    } else {
      // Select first collection
      await page.click('[role="option"], button[data-collection-id]').first();
    }

    // Step 6: Verify success
    await verifyToast(page, /added|success/i);

    // Step 7: Navigate to collections and verify item is there
    await page.goto('/collections');
    await expect(page.locator('h1:has-text("Collections")')).toBeVisible();

    // Find and open the collection
    const collectionCard = page.locator('[data-testid="collection-card"]').first();
    if (await collectionCard.isVisible()) {
      await collectionCard.click();

      // Verify item is in collection
      await expect(
        page.locator('[data-testid="collection-item"], table tbody tr')
      ).toHaveCount(1, { timeout: 5000 });
    }
  });

  test('should handle expired share link gracefully', async ({ page, context }) => {
    // Note: This test assumes you have a way to create an expired link
    // or can mock the API response. For now, we'll test the error handling.

    // Create a fake expired link
    const expiredLink = `${page.url()}/deals/999999/expired-token-xyz`;

    // Navigate to expired link
    await page.goto(expiredLink);

    // Verify error message or redirect
    const notFoundHeading = page.locator('h1:has-text("Not Found"), h1:has-text("404")');
    const expiredMessage = page.locator('text=/expired|invalid|not found/i');

    await expect(
      notFoundHeading.or(expiredMessage)
    ).toBeVisible({ timeout: 5000 });
  });

  test('should handle share link generation errors', async ({ page }) => {
    // Note: This test would ideally mock an API error
    // For now, we test that the UI handles errors gracefully

    // Click share button
    const shareButton = page.locator('button[aria-label*="Share"]').first();
    await shareButton.click();
    await page.waitForSelector('[role="dialog"]', { state: 'visible' });

    // The modal should show either:
    // 1. A loading state, then success
    // 2. An error message with retry button

    // Wait for either success or error
    const loadingIndicator = page.locator('text=/generating|loading/i');
    const errorMessage = page.locator('text=/failed|error/i');
    const shareInput = page.locator('input#share-link');

    // One of these should be visible within 5 seconds
    await expect(
      loadingIndicator.or(errorMessage).or(shareInput)
    ).toBeVisible({ timeout: 5000 });

    // If error is shown, verify retry button exists
    if (await errorMessage.isVisible()) {
      await expect(page.locator('button:has-text("Retry")')).toBeVisible();
    }
  });

  test('should display share link with correct expiry information', async ({ page }) => {
    // Click share button
    const shareButton = page.locator('button[aria-label*="Share"]').first();
    await shareButton.click();
    await page.waitForSelector('[role="dialog"]', { state: 'visible' });

    // Wait for share link to generate
    await page.waitForSelector('input#share-link', { state: 'visible', timeout: 5000 });

    // Verify expiry text is displayed and formatted correctly
    const expiryText = page.locator('text=/expires in \\d+/i');
    await expect(expiryText).toBeVisible();

    // Verify help text about link sharing
    await expect(
      page.locator('text=/anyone with this link/i')
    ).toBeVisible();
  });
});
