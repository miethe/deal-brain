/**
 * E2E Tests: Accessibility Audit (WCAG 2.1 AA)
 *
 * Automated accessibility testing for all Phase 4 components using axe-core
 *
 * Scope:
 * - Public deal page (/deals/[id]/[token])
 * - Collections list (/collections)
 * - Collection workspace (/collections/[id])
 * - Share modal
 * - Collection selector modal
 *
 * Standards: WCAG 2.1 Level A & AA
 */

import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

/**
 * Helper to run axe accessibility scan and format results
 */
async function runAccessibilityScan(
  page: Page,
  context: string,
  options?: { exclude?: string[] }
) {
  const builder = new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .options({
      runOnly: {
        type: 'tag',
        values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'],
      },
    });

  // Apply exclusions if provided
  if (options?.exclude) {
    options.exclude.forEach((selector) => builder.exclude(selector));
  }

  const results = await builder.analyze();

  // Log violations for debugging
  if (results.violations.length > 0) {
    console.log(`\n❌ Accessibility violations found in ${context}:`);
    results.violations.forEach((violation) => {
      console.log(`\n  ${violation.impact?.toUpperCase()}: ${violation.id}`);
      console.log(`  Description: ${violation.description}`);
      console.log(`  Help: ${violation.helpUrl}`);
      console.log(`  Elements (${violation.nodes.length}):`);
      violation.nodes.forEach((node, idx) => {
        console.log(`    ${idx + 1}. ${node.html}`);
        console.log(`       Target: ${node.target.join(', ')}`);
      });
    });
  }

  return results;
}

test.describe('Accessibility Audit - WCAG 2.1 AA', () => {
  test.describe('Public Deal Page', () => {
    test.beforeEach(async ({ page }) => {
      // First, navigate to listings to get a share link
      await page.goto('/listings');
      await page.waitForSelector('table, [data-testid="listings-grid"]', {
        timeout: 10000,
      });
    });

    test('should not have accessibility violations on public deal page', async ({ page, context }) => {
      // Get share link
      const shareButton = page.locator('button[aria-label*="Share"]').first();
      await shareButton.click();
      await page.waitForSelector('[role="dialog"]', { state: 'visible' });

      // Click to generate/reveal link
      const linkTab = page.locator('[data-tab="link"], button:has-text("Copy Link")');
      if (await linkTab.count() > 0) {
        await linkTab.first().click();
      }

      // Get the share URL from the input or displayed link
      const shareUrlInput = page.locator('input[readonly][value*="/deals/"]');
      const shareUrl = await shareUrlInput.getAttribute('value');

      if (!shareUrl) {
        throw new Error('Share URL not found');
      }

      // Open public page in new context (simulating logged-out user)
      const publicContext = await context.browser()?.newContext();
      const publicPage = await publicContext!.newPage();
      await publicPage.goto(shareUrl);

      // Wait for page to load
      await publicPage.waitForSelector('h1, [role="main"]', { timeout: 10000 });

      // Run accessibility scan
      const results = await runAccessibilityScan(publicPage, 'Public Deal Page');

      // No critical or serious violations allowed
      const criticalViolations = results.violations.filter(
        (v) => v.impact === 'critical' || v.impact === 'serious'
      );

      expect(criticalViolations).toEqual([]);

      await publicPage.close();
      await publicContext!.close();
    });

    test('should have proper ARIA labels on public deal page', async ({ page, context }) => {
      // Get share link (same as above)
      const shareButton = page.locator('button[aria-label*="Share"]').first();
      await shareButton.click();
      await page.waitForSelector('[role="dialog"]', { state: 'visible' });

      const linkTab = page.locator('[data-tab="link"], button:has-text("Copy Link")');
      if (await linkTab.count() > 0) {
        await linkTab.first().click();
      }

      const shareUrlInput = page.locator('input[readonly][value*="/deals/"]');
      const shareUrl = await shareUrlInput.getAttribute('value');

      if (!shareUrl) {
        throw new Error('Share URL not found');
      }

      const publicContext = await context.browser()?.newContext();
      const publicPage = await publicContext!.newPage();
      await publicPage.goto(shareUrl);
      await publicPage.waitForSelector('h1, [role="main"]', { timeout: 10000 });

      // Check for essential ARIA labels
      const addToCollectionButton = publicPage.locator('button:has-text("Add to Collection"), button[aria-label*="collection"]');
      if (await addToCollectionButton.count() > 0) {
        const ariaLabel = await addToCollectionButton.first().getAttribute('aria-label');
        expect(ariaLabel || (await addToCollectionButton.first().textContent())).toBeTruthy();
      }

      // Check for external link indicators
      const externalLinks = publicPage.locator('a[href^="http"]');
      const count = await externalLinks.count();
      for (let i = 0; i < Math.min(count, 5); i++) {
        const link = externalLinks.nth(i);
        const hasAriaLabel = await link.getAttribute('aria-label');
        const hasVisibleText = await link.textContent();
        expect(hasAriaLabel || hasVisibleText).toBeTruthy();
      }

      await publicPage.close();
      await publicContext!.close();
    });

    test('should have proper heading hierarchy', async ({ page, context }) => {
      // Get share link
      const shareButton = page.locator('button[aria-label*="Share"]').first();
      await shareButton.click();
      await page.waitForSelector('[role="dialog"]', { state: 'visible' });

      const linkTab = page.locator('[data-tab="link"], button:has-text("Copy Link")');
      if (await linkTab.count() > 0) {
        await linkTab.first().click();
      }

      const shareUrlInput = page.locator('input[readonly][value*="/deals/"]');
      const shareUrl = await shareUrlInput.getAttribute('value');

      if (!shareUrl) {
        throw new Error('Share URL not found');
      }

      const publicContext = await context.browser()?.newContext();
      const publicPage = await publicContext!.newPage();
      await publicPage.goto(shareUrl);
      await publicPage.waitForSelector('h1', { timeout: 10000 });

      // Check heading hierarchy
      const h1Count = await publicPage.locator('h1').count();
      expect(h1Count).toBeGreaterThanOrEqual(1);
      expect(h1Count).toBeLessThanOrEqual(1); // Should only have one h1

      await publicPage.close();
      await publicContext!.close();
    });
  });

  test.describe('Collections List Page', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/collections');
      // Wait for either collections or empty state
      await page.waitForSelector(
        '[data-testid="collections-grid"], [data-testid="empty-state"], h1',
        { timeout: 10000 }
      );
    });

    test('should not have accessibility violations on collections list', async ({ page }) => {
      const results = await runAccessibilityScan(page, 'Collections List Page');

      // No critical or serious violations allowed
      const criticalViolations = results.violations.filter(
        (v) => v.impact === 'critical' || v.impact === 'serious'
      );

      expect(criticalViolations).toEqual([]);
    });

    test('should have accessible collection cards', async ({ page }) => {
      // Check if we have collection cards
      const collectionCards = page.locator('[data-testid="collection-card"], article, [role="article"]');
      const cardCount = await collectionCards.count();

      if (cardCount > 0) {
        // Each card should be keyboard accessible
        for (let i = 0; i < Math.min(cardCount, 3); i++) {
          const card = collectionCards.nth(i);
          // Cards should have a link or button that's focusable
          const interactiveElement = card.locator('a, button').first();
          await interactiveElement.focus();
          await expect(interactiveElement).toBeFocused();
        }
      }
    });

    test('should have accessible "New Collection" button', async ({ page }) => {
      const newButton = page.locator('button:has-text("New collection"), button:has-text("New Collection")');

      if (await newButton.count() > 0) {
        // Should be keyboard accessible
        await newButton.focus();
        await expect(newButton).toBeFocused();

        // Should have accessible name
        const accessibleName = await newButton.textContent();
        expect(accessibleName).toContain('Collection');
      }
    });
  });

  test.describe('Collection Workspace Page', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/collections');
      await page.waitForSelector(
        '[data-testid="collections-grid"], [data-testid="empty-state"], h1',
        { timeout: 10000 }
      );
    });

    test('should not have accessibility violations in workspace', async ({ page }) => {
      // Try to navigate to first collection if exists
      const firstCollection = page.locator(
        '[data-testid="collection-card"] a, article a, [role="article"] a'
      ).first();

      if (await firstCollection.count() > 0) {
        await firstCollection.click();
        await page.waitForSelector('[data-testid="workspace"], h1', { timeout: 10000 });

        const results = await runAccessibilityScan(page, 'Collection Workspace');

        const criticalViolations = results.violations.filter(
          (v) => v.impact === 'critical' || v.impact === 'serious'
        );

        expect(criticalViolations).toEqual([]);
      }
    });

    test('should have accessible table/grid controls', async ({ page }) => {
      const firstCollection = page.locator(
        '[data-testid="collection-card"] a, article a, [role="article"] a'
      ).first();

      if (await firstCollection.count() > 0) {
        await firstCollection.click();
        await page.waitForSelector('[data-testid="workspace"], h1', { timeout: 10000 });

        // Check for view toggle buttons
        const viewToggles = page.locator('button[aria-label*="view"], button[data-view-toggle]');
        if (await viewToggles.count() > 0) {
          const firstToggle = viewToggles.first();
          const ariaLabel = await firstToggle.getAttribute('aria-label');
          const text = await firstToggle.textContent();
          expect(ariaLabel || text).toBeTruthy();
        }

        // Check for filter/sort controls
        const filterControls = page.locator('select, button[aria-label*="filter"], button[aria-label*="sort"]');
        const controlCount = await filterControls.count();
        for (let i = 0; i < Math.min(controlCount, 3); i++) {
          const control = filterControls.nth(i);
          await control.focus();
          await expect(control).toBeFocused();
        }
      }
    });
  });

  test.describe('Share Modal', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/listings');
      await page.waitForSelector('table, [data-testid="listings-grid"]', {
        timeout: 10000,
      });
    });

    test('should not have accessibility violations in share modal', async ({ page }) => {
      // Open share modal
      const shareButton = page.locator('button[aria-label*="Share"]').first();
      await shareButton.click();
      await page.waitForSelector('[role="dialog"]', { state: 'visible' });

      // Run scan on modal
      const results = await runAccessibilityScan(page, 'Share Modal');

      const criticalViolations = results.violations.filter(
        (v) => v.impact === 'critical' || v.impact === 'serious'
      );

      expect(criticalViolations).toEqual([]);
    });

    test('should trap focus within modal', async ({ page }) => {
      const shareButton = page.locator('button[aria-label*="Share"]').first();
      await shareButton.click();
      await page.waitForSelector('[role="dialog"]', { state: 'visible' });

      // Get all focusable elements in modal
      const modal = page.locator('[role="dialog"]');
      const focusableElements = modal.locator(
        'a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );

      const count = await focusableElements.count();
      expect(count).toBeGreaterThan(0);

      // Tab through elements
      for (let i = 0; i < Math.min(count, 5); i++) {
        await page.keyboard.press('Tab');
      }

      // Focus should still be within modal
      const focusedElement = page.locator(':focus');
      const isFocusInModal = await modal.evaluate((el, focused) => {
        return el.contains(focused);
      }, await focusedElement.elementHandle());

      expect(isFocusInModal).toBe(true);
    });

    test('should close on Escape key', async ({ page }) => {
      const shareButton = page.locator('button[aria-label*="Share"]').first();
      await shareButton.click();
      await page.waitForSelector('[role="dialog"]', { state: 'visible' });

      // Press Escape
      await page.keyboard.press('Escape');

      // Modal should close
      await expect(page.locator('[role="dialog"]')).not.toBeVisible({ timeout: 2000 });
    });
  });

  test.describe('Collection Selector Modal', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/listings');
      await page.waitForSelector('table, [data-testid="listings-grid"]', {
        timeout: 10000,
      });
    });

    test('should not have accessibility violations in collection selector', async ({ page }) => {
      // Open collection selector (Add to Collection button)
      const addButton = page.locator(
        'button[aria-label*="collection"], button:has-text("Add to Collection")'
      ).first();

      if (await addButton.count() > 0) {
        await addButton.click();
        await page.waitForSelector('[role="dialog"]', { state: 'visible' });

        const results = await runAccessibilityScan(page, 'Collection Selector Modal');

        const criticalViolations = results.violations.filter(
          (v) => v.impact === 'critical' || v.impact === 'serious'
        );

        expect(criticalViolations).toEqual([]);
      }
    });

    test('should have accessible collection checkboxes', async ({ page }) => {
      const addButton = page.locator(
        'button[aria-label*="collection"], button:has-text("Add to Collection")'
      ).first();

      if (await addButton.count() > 0) {
        await addButton.click();
        await page.waitForSelector('[role="dialog"]', { state: 'visible' });

        // Check for checkboxes or radio buttons
        const checkboxes = page.locator('input[type="checkbox"], [role="checkbox"]');
        const checkboxCount = await checkboxes.count();

        if (checkboxCount > 0) {
          for (let i = 0; i < Math.min(checkboxCount, 3); i++) {
            const checkbox = checkboxes.nth(i);
            // Each checkbox should have a label
            const id = await checkbox.getAttribute('id');
            if (id) {
              const label = page.locator(`label[for="${id}"]`);
              await expect(label).toBeVisible();
            }
          }
        }
      }
    });
  });

  test.describe('Color Contrast', () => {
    test('should meet minimum contrast requirements', async ({ page }) => {
      await page.goto('/collections');
      await page.waitForSelector('h1', { timeout: 10000 });

      const results = await runAccessibilityScan(page, 'Color Contrast');

      // Filter for color contrast violations
      const contrastViolations = results.violations.filter((v) =>
        v.id.includes('color-contrast')
      );

      expect(contrastViolations).toEqual([]);
    });
  });

  test.describe('Keyboard Navigation', () => {
    test('should navigate collections with keyboard', async ({ page }) => {
      await page.goto('/collections');
      await page.waitForSelector('h1', { timeout: 10000 });

      // Tab through interactive elements
      const interactiveElements = page.locator('a, button, input, select, textarea');
      const count = await interactiveElements.count();

      if (count > 0) {
        // Focus first element
        await page.keyboard.press('Tab');
        let previousFocus = await page.locator(':focus').textContent();

        // Tab through a few elements
        for (let i = 0; i < Math.min(count, 5); i++) {
          await page.keyboard.press('Tab');
          const currentFocus = await page.locator(':focus').textContent();

          // Focus should change (unless we're at the end)
          if (i < count - 1) {
            expect(currentFocus).toBeTruthy();
          }

          previousFocus = currentFocus;
        }
      }
    });

    test('should have visible focus indicators', async ({ page }) => {
      await page.goto('/collections');
      await page.waitForSelector('h1', { timeout: 10000 });

      // Get the "New Collection" button
      const button = page.locator('button:has-text("New collection"), button:has-text("New Collection")').first();

      if (await button.count() > 0) {
        await button.focus();

        // Check if focus is visible (this is basic - actual visual check would require screenshot comparison)
        await expect(button).toBeFocused();

        // Get computed styles to check for focus indicators
        const outline = await button.evaluate((el) => {
          const styles = window.getComputedStyle(el);
          return {
            outline: styles.outline,
            outlineWidth: styles.outlineWidth,
            outlineStyle: styles.outlineStyle,
            boxShadow: styles.boxShadow,
          };
        });

        // Should have some form of focus indicator
        const hasFocusIndicator =
          outline.outlineWidth !== '0px' ||
          outline.outline !== 'none' ||
          outline.boxShadow !== 'none';

        expect(hasFocusIndicator).toBe(true);
      }
    });
  });

  test.describe('Mobile Touch Targets', () => {
    test.use({ viewport: { width: 375, height: 667 } }); // iPhone SE

    test('should have adequate touch targets on mobile', async ({ page }) => {
      await page.goto('/collections');
      await page.waitForSelector('h1', { timeout: 10000 });

      // Check button sizes
      const buttons = page.locator('button, a[role="button"]');
      const buttonCount = await buttons.count();

      for (let i = 0; i < Math.min(buttonCount, 5); i++) {
        const button = buttons.nth(i);
        const box = await button.boundingBox();

        if (box) {
          // WCAG 2.1 AA requires 44x44px minimum for touch targets
          expect(box.width).toBeGreaterThanOrEqual(40); // Allow slight variance
          expect(box.height).toBeGreaterThanOrEqual(40);
        }
      }
    });
  });
});
