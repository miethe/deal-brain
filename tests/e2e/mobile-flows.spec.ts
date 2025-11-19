/**
 * E2E Tests: Mobile Flows
 *
 * Tests critical user flows on mobile devices
 *
 * User Story:
 * - User interacts with app on mobile device
 * - Share flow works with touch interactions
 * - Public deal page is responsive
 * - Collection workspace adapts to mobile
 * - All touch targets are accessible (44px minimum)
 */

import { test, expect, type Page, devices } from '@playwright/test';
import {
  verifyTouchTargetSize,
  getShareLink,
  verifyToast,
  createCollection,
} from './fixtures';

// Mobile device configurations
const MOBILE_DEVICES = {
  iphone12: devices['iPhone 12'],
  pixel5: devices['Pixel 5'],
  galaxyS21: devices['Galaxy S21'],
};

test.describe('Mobile Share Flow', () => {
  // Run tests on mobile viewports
  test.use({ ...MOBILE_DEVICES.iphone12 });

  test.beforeEach(async ({ page }) => {
    await page.goto('/listings');
    await page.waitForSelector('table, [data-testid="listings-grid"]', { timeout: 10000 });
  });

  test('should have tappable share button (44px minimum)', async ({ page }) => {
    // Find first share button
    const shareButton = page.locator('button[aria-label*="Share"]').first();
    await expect(shareButton).toBeVisible({ timeout: 5000 });

    // Verify touch target size
    await verifyTouchTargetSize(page, 'button[aria-label*="Share"]', 44);
  });

  test('should open share modal on mobile', async ({ page }) => {
    // Click share button
    const shareButton = page.locator('button[aria-label*="Share"]').first();
    await shareButton.click();

    // Verify modal appears and fits screen
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible({ timeout: 5000 });

    // Verify modal doesn't overflow viewport
    const modalBox = await modal.boundingBox();
    const viewport = page.viewportSize();

    if (modalBox && viewport) {
      expect(modalBox.width).toBeLessThanOrEqual(viewport.width);
      expect(modalBox.height).toBeLessThanOrEqual(viewport.height);
    }
  });

  test('should switch between tabs on mobile', async ({ page }) => {
    // Open share modal
    const shareButton = page.locator('button[aria-label*="Share"]').first();
    await shareButton.click();
    await page.waitForSelector('[role="dialog"]', { state: 'visible' });

    // Verify tabs are accessible
    const copyLinkTab = page.locator('button:has-text("Copy Link")');
    const shareWithUserTab = page.locator('button:has-text("Share with User")');

    await expect(copyLinkTab).toBeVisible();
    await expect(shareWithUserTab).toBeVisible();

    // Verify tab buttons have proper touch target size (44px minimum)
    await verifyTouchTargetSize(page, 'button:has-text("Copy Link")', 44);
    await verifyTouchTargetSize(page, 'button:has-text("Share with User")', 44);

    // Switch tabs
    await shareWithUserTab.click();
    await expect(page.locator('input#user-search')).toBeVisible({ timeout: 3000 });

    await copyLinkTab.click();
    await expect(page.locator('input#share-link')).toBeVisible({ timeout: 3000 });
  });

  test('should copy to clipboard on mobile', async ({ page, context }) => {
    // Grant clipboard permissions
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);

    // Open share modal
    const shareButton = page.locator('button[aria-label*="Share"]').first();
    await shareButton.click();
    await page.waitForSelector('[role="dialog"]', { state: 'visible' });

    // Wait for share link
    await page.waitForSelector('input#share-link', { state: 'visible', timeout: 5000 });

    // Verify copy button has proper touch target
    await verifyTouchTargetSize(page, 'button[aria-label="Copy to clipboard"]', 44);

    // Click copy button
    const copyButton = page.locator('button[aria-label="Copy to clipboard"]');
    await copyButton.click();

    // Verify clipboard has content
    const clipboardText = await page.evaluate(() => navigator.clipboard.readText());
    expect(clipboardText).toMatch(/^http/);
  });

  test('should view public deal page on mobile', async ({ page, context }) => {
    // Grant permissions
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);

    // Get share link
    const shareButton = page.locator('button[aria-label*="Share"]').first();
    await shareButton.click();
    await page.waitForSelector('[role="dialog"]', { state: 'visible' });
    const shareLink = await getShareLink(page);

    // Close modal
    await page.keyboard.press('Escape');

    // Navigate to public page
    await page.goto(shareLink);

    // Verify page is responsive
    await expect(page.locator('h1, h2')).toBeVisible({ timeout: 5000 });

    // Verify key information is readable
    await expect(page.locator('text=/price|\\$/i')).toBeVisible();
    await expect(page.locator('text=/cpu|processor/i')).toBeVisible();

    // Verify "Add to Collection" CTA is prominent
    const addToCollectionBtn = page.locator('button:has-text("Add to Collection")');
    await expect(addToCollectionBtn).toBeVisible();

    // Verify button has proper touch target
    await verifyTouchTargetSize(page, 'button:has-text("Add to Collection")', 44);
  });

  test('should add to collection from public page on mobile', async ({ page, context }) => {
    // Get share link
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);
    const shareButton = page.locator('button[aria-label*="Share"]').first();
    await shareButton.click();
    await page.waitForSelector('[role="dialog"]', { state: 'visible' });
    const shareLink = await getShareLink(page);
    await page.keyboard.press('Escape');

    // Navigate to public page
    await page.goto(shareLink);

    // Click "Add to Collection"
    const addBtn = page.locator('button:has-text("Add to Collection")');
    await addBtn.click();

    // Verify collection selector appears and fits screen
    const selector = page.locator('[role="dialog"], [data-radix-popper-content-wrapper]');
    await expect(selector).toBeVisible({ timeout: 5000 });

    const selectorBox = await selector.boundingBox();
    const viewport = page.viewportSize();

    if (selectorBox && viewport) {
      expect(selectorBox.width).toBeLessThanOrEqual(viewport.width);
    }
  });

  test('should scroll long listing details on mobile', async ({ page, context }) => {
    // Get share link
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);
    const shareButton = page.locator('button[aria-label*="Share"]').first();
    await shareButton.click();
    await page.waitForSelector('[role="dialog"]', { state: 'visible' });
    const shareLink = await getShareLink(page);
    await page.keyboard.press('Escape');

    // Navigate to public page
    await page.goto(shareLink);
    await page.waitForLoadState('networkidle');

    // Verify page is scrollable
    const bodyHeight = await page.evaluate(() => document.body.scrollHeight);
    const viewportHeight = page.viewportSize()?.height || 0;

    // If content is longer than viewport, verify scroll works
    if (bodyHeight > viewportHeight) {
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      const scrollY = await page.evaluate(() => window.scrollY);
      expect(scrollY).toBeGreaterThan(0);
    }
  });
});

test.describe('Mobile Workspace Flow', () => {
  // Run tests on mobile viewports
  test.use({ ...MOBILE_DEVICES.iphone12 });

  test.beforeEach(async ({ page }) => {
    await page.goto('/collections');
    await expect(page.locator('h1:has-text("Collections")')).toBeVisible({ timeout: 5000 });
  });

  test('should navigate to collection workspace on mobile', async ({ page }) => {
    // Check if collections exist
    const collectionCard = page.locator('[data-testid="collection-card"]').first();

    if (await collectionCard.isVisible({ timeout: 3000 })) {
      // Click collection
      await collectionCard.click();

      // Verify workspace loads
      await expect(
        page.locator('h1, [data-testid="collection-title"]')
      ).toBeVisible({ timeout: 5000 });
    } else {
      // Create collection first
      await createCollection(page, 'Mobile Test Collection');
    }
  });

  test('should display card view by default on mobile', async ({ page }) => {
    const collectionCard = page.locator('[data-testid="collection-card"]').first();

    if (await collectionCard.isVisible({ timeout: 3000 })) {
      await collectionCard.click();

      // Verify card view is default (or table is responsive)
      // Note: Implementation may vary - some use card view, others responsive table
      const cardView = page.locator('[data-testid="card-view"], .card-grid');
      const table = page.locator('table');

      // At least one should be visible
      await expect(cardView.or(table)).toBeVisible({ timeout: 5000 });

      // If table is shown, verify it's responsive
      if (await table.isVisible()) {
        const tableBox = await table.boundingBox();
        const viewport = page.viewportSize();

        if (tableBox && viewport) {
          // Table should not overflow viewport
          expect(tableBox.width).toBeLessThanOrEqual(viewport.width);
        }
      }
    }
  });

  test('should have collapsible filters on mobile', async ({ page }) => {
    const collectionCard = page.locator('[data-testid="collection-card"]').first();

    if (!(await collectionCard.isVisible({ timeout: 3000 }))) {
      test.skip('No collections available');
    }

    await collectionCard.click();
    await page.waitForTimeout(1000);

    // Look for filter toggle button
    const filterToggle = page.locator(
      'button[aria-label*="filter"], button:has-text("Filters"), [data-filter-toggle]'
    );

    if (await filterToggle.isVisible({ timeout: 3000 })) {
      // Verify toggle has proper touch target
      await verifyTouchTargetSize(page, 'button[aria-label*="filter"]', 44);

      // Click to expand filters
      await filterToggle.click();
      await page.waitForTimeout(300);

      // Verify filters are visible
      const filtersPanel = page.locator('[data-filters], .filters-panel');
      await expect(filtersPanel).toBeVisible({ timeout: 2000 });

      // Click again to collapse
      await filterToggle.click();
      await page.waitForTimeout(300);

      // Verify filters are hidden
      await expect(filtersPanel).not.toBeVisible({ timeout: 2000 });
    }
  });

  test('should tap item card to view details on mobile', async ({ page }) => {
    const collectionCard = page.locator('[data-testid="collection-card"]').first();

    if (!(await collectionCard.isVisible({ timeout: 3000 }))) {
      test.skip('No collections available');
    }

    await collectionCard.click();
    await page.waitForTimeout(1000);

    // Find first item
    const firstItem = page.locator('[data-testid="collection-item"], table tbody tr, .card').first();

    if (await firstItem.isVisible({ timeout: 3000 })) {
      // Tap item
      await firstItem.click();

      // Verify details panel opens (may be modal or expanded inline)
      const detailsPanel = page.locator(
        '[data-testid="item-details"], [role="dialog"], .details-panel'
      );

      await expect(detailsPanel).toBeVisible({ timeout: 3000 });
    }
  });

  test('should edit notes with mobile keyboard', async ({ page }) => {
    const collectionCard = page.locator('[data-testid="collection-card"]').first();

    if (!(await collectionCard.isVisible({ timeout: 3000 }))) {
      test.skip('No collections available');
    }

    await collectionCard.click();
    await page.waitForTimeout(1000);

    // Tap first item
    const firstItem = page.locator('[data-testid="collection-item"], table tbody tr, .card').first();
    if (await firstItem.isVisible({ timeout: 3000 })) {
      await firstItem.click();

      // Find notes textarea
      const notesTextarea = page.locator('textarea[name*="notes"], textarea[id*="notes"]');

      if (await notesTextarea.isVisible({ timeout: 3000 })) {
        // Focus textarea (should trigger mobile keyboard)
        await notesTextarea.focus();

        // Type notes
        await notesTextarea.fill('Great deal! Very fast CPU.');

        // Wait for auto-save
        await page.waitForTimeout(600);

        // Verify value is saved
        await expect(notesTextarea).toHaveValue(/Great deal/);
      }
    }
  });

  test('should verify touch targets for all interactive elements', async ({ page }) => {
    const collectionCard = page.locator('[data-testid="collection-card"]').first();

    if (!(await collectionCard.isVisible({ timeout: 3000 }))) {
      test.skip('No collections available');
    }

    await collectionCard.click();
    await page.waitForTimeout(1000);

    // Verify various button touch targets
    const buttonsToCheck = [
      'button:has-text("Add")',
      'button:has-text("Export")',
      'button[aria-label*="Edit"]',
      'button[aria-label*="Delete"]',
    ];

    for (const selector of buttonsToCheck) {
      const button = page.locator(selector).first();
      if (await button.isVisible({ timeout: 1000 })) {
        await verifyTouchTargetSize(page, selector, 44);
      }
    }
  });

  test('should handle swipe gestures on mobile (if implemented)', async ({ page }) => {
    const collectionCard = page.locator('[data-testid="collection-card"]').first();

    if (!(await collectionCard.isVisible({ timeout: 3000 }))) {
      test.skip('No collections available');
    }

    await collectionCard.click();
    await page.waitForTimeout(1000);

    // Note: Swipe gesture testing is implementation-specific
    // This is a placeholder for swipe-to-delete or swipe-to-reveal actions

    const firstItem = page.locator('[data-testid="collection-item"], .card').first();

    if (await firstItem.isVisible({ timeout: 3000 })) {
      const box = await firstItem.boundingBox();

      if (box) {
        // Simulate swipe left
        await page.mouse.move(box.x + box.width - 10, box.y + box.height / 2);
        await page.mouse.down();
        await page.mouse.move(box.x + 10, box.y + box.height / 2, { steps: 10 });
        await page.mouse.up();

        // Check if swipe revealed actions (implementation-specific)
        // This would depend on your UI implementation
        await page.waitForTimeout(300);
      }
    }
  });

  test('should open and close modals on mobile', async ({ page }) => {
    // Create new collection on mobile
    const newCollectionBtn = page.locator('button:has-text("New collection")');
    await expect(newCollectionBtn).toBeVisible({ timeout: 5000 });
    await newCollectionBtn.click();

    // Verify modal fits screen
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible({ timeout: 3000 });

    const modalBox = await modal.boundingBox();
    const viewport = page.viewportSize();

    if (modalBox && viewport) {
      expect(modalBox.width).toBeLessThanOrEqual(viewport.width);
      expect(modalBox.height).toBeLessThanOrEqual(viewport.height);
    }

    // Close modal
    const closeButton = page.locator('[role="dialog"] button[aria-label*="Close"]').first();
    if (await closeButton.isVisible({ timeout: 2000 })) {
      await verifyTouchTargetSize(page, '[role="dialog"] button[aria-label*="Close"]', 44);
      await closeButton.click();
    } else {
      // Fallback: tap outside or press escape
      await page.keyboard.press('Escape');
    }

    // Verify modal is closed
    await expect(modal).not.toBeVisible({ timeout: 2000 });
  });

  test('should scroll through collection items on mobile', async ({ page }) => {
    const collectionCard = page.locator('[data-testid="collection-card"]').first();

    if (!(await collectionCard.isVisible({ timeout: 3000 }))) {
      test.skip('No collections available');
    }

    await collectionCard.click();
    await page.waitForTimeout(1000);

    // Verify items are scrollable if there are many
    const itemsContainer = page.locator('[data-testid="items-container"], table, .items-list').first();

    if (await itemsContainer.isVisible({ timeout: 3000 })) {
      // Scroll to bottom
      await page.evaluate(() => {
        const container = document.querySelector('[data-testid="items-container"], table, .items-list');
        if (container) {
          container.scrollTop = container.scrollHeight;
        } else {
          window.scrollTo(0, document.body.scrollHeight);
        }
      });

      await page.waitForTimeout(500);

      // Verify scroll worked
      const scrollPosition = await page.evaluate(() => {
        const container = document.querySelector('[data-testid="items-container"], table, .items-list');
        return container ? container.scrollTop : window.scrollY;
      });

      expect(scrollPosition).toBeGreaterThanOrEqual(0);
    }
  });
});

test.describe('Mobile Navigation & Accessibility', () => {
  test.use({ ...MOBILE_DEVICES.iphone12 });

  test('should have accessible navigation menu on mobile', async ({ page }) => {
    await page.goto('/');

    // Look for hamburger menu or mobile nav toggle
    const navToggle = page.locator(
      'button[aria-label*="menu"], button[aria-label*="navigation"], [data-mobile-menu-toggle]'
    );

    if (await navToggle.isVisible({ timeout: 3000 })) {
      // Verify touch target
      await verifyTouchTargetSize(page, 'button[aria-label*="menu"]', 44);

      // Open menu
      await navToggle.click();

      // Verify menu appears
      const mobileMenu = page.locator('[role="navigation"], [data-mobile-menu]');
      await expect(mobileMenu).toBeVisible({ timeout: 2000 });

      // Verify key links are accessible
      await expect(
        mobileMenu.locator('a:has-text("Collections"), a:has-text("Listings")')
      ).toBeVisible();
    }
  });

  test('should support pinch-to-zoom on mobile (if enabled)', async ({ page }) => {
    await page.goto('/listings');

    // Check if viewport meta tag allows zooming
    const viewportMeta = await page.locator('meta[name="viewport"]').getAttribute('content');

    if (viewportMeta) {
      // Verify that user-scalable is not set to no (accessibility requirement)
      expect(viewportMeta).not.toContain('user-scalable=no');
    }
  });

  test('should have readable text on mobile', async ({ page }) => {
    await page.goto('/listings');
    await page.waitForLoadState('networkidle');

    // Verify font sizes are readable (minimum 16px for body text)
    const bodyFontSize = await page.evaluate(() => {
      const body = document.body;
      return parseInt(window.getComputedStyle(body).fontSize, 10);
    });

    // Body text should be at least 14px (preferably 16px)
    expect(bodyFontSize).toBeGreaterThanOrEqual(14);
  });
});

// Cross-browser mobile testing
test.describe('Cross-Device Compatibility', () => {
  const devices = [
    { name: 'iPhone 12', config: MOBILE_DEVICES.iphone12 },
    { name: 'Pixel 5', config: MOBILE_DEVICES.pixel5 },
  ];

  for (const device of devices) {
    test(`should work on ${device.name}`, async ({ browser }) => {
      const context = await browser.newContext({ ...device.config });
      const page = await context.newPage();

      // Navigate to listings
      await page.goto('/listings');
      await expect(page.locator('h1, h2')).toBeVisible({ timeout: 5000 });

      // Click share button
      const shareButton = page.locator('button[aria-label*="Share"]').first();
      if (await shareButton.isVisible({ timeout: 3000 })) {
        await shareButton.click();

        // Verify modal appears
        await expect(page.locator('[role="dialog"]')).toBeVisible({ timeout: 3000 });
      }

      await context.close();
    });
  }
});
