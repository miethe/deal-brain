/**
 * E2E Test Fixtures and Helpers
 *
 * Provides reusable utilities for seeding test data and common test operations
 */

import { Page, expect } from '@playwright/test';

export interface TestUser {
  id: number;
  username: string;
  email: string;
  password: string;
}

export interface TestListing {
  id: number;
  title: string;
  price: number;
  cpu_name: string;
}

/**
 * Test data fixtures
 */
export const TEST_USERS: Record<string, TestUser> = {
  userA: {
    id: 1,
    username: 'testuser_a',
    email: 'usera@test.com',
    password: 'testpass123',
  },
  userB: {
    id: 2,
    username: 'testuser_b',
    email: 'userb@test.com',
    password: 'testpass123',
  },
};

/**
 * Helper to wait for API response with timeout
 */
export async function waitForApiResponse(
  page: Page,
  urlPattern: string | RegExp,
  timeout: number = 5000
) {
  return await page.waitForResponse(
    (response) => {
      const url = response.url();
      const matches = typeof urlPattern === 'string'
        ? url.includes(urlPattern)
        : urlPattern.test(url);
      return matches && response.status() === 200;
    },
    { timeout }
  );
}

/**
 * Helper to measure response time
 */
export async function measureResponseTime(
  page: Page,
  action: () => Promise<void>,
  urlPattern: string | RegExp
): Promise<number> {
  const startTime = Date.now();

  const responsePromise = page.waitForResponse(
    (response) => {
      const url = response.url();
      const matches = typeof urlPattern === 'string'
        ? url.includes(urlPattern)
        : urlPattern.test(url);
      return matches;
    }
  );

  await action();
  await responsePromise;

  return Date.now() - startTime;
}

/**
 * Helper to verify OpenGraph meta tags
 */
export async function verifyOGTags(
  page: Page,
  expectedTags: {
    title?: string;
    description?: string;
    image?: boolean;
    url?: string;
  }
) {
  if (expectedTags.title) {
    const ogTitle = await page.locator('meta[property="og:title"]').getAttribute('content');
    expect(ogTitle).toBeTruthy();
    if (expectedTags.title !== '*') {
      expect(ogTitle).toContain(expectedTags.title);
    }
  }

  if (expectedTags.description) {
    const ogDesc = await page.locator('meta[property="og:description"]').getAttribute('content');
    expect(ogDesc).toBeTruthy();
  }

  if (expectedTags.image) {
    const ogImage = await page.locator('meta[property="og:image"]').getAttribute('content');
    expect(ogImage).toBeTruthy();
  }

  if (expectedTags.url) {
    const ogUrl = await page.locator('meta[property="og:url"]').getAttribute('content');
    expect(ogUrl).toBeTruthy();
    if (expectedTags.url !== '*') {
      expect(ogUrl).toContain(expectedTags.url);
    }
  }
}

/**
 * Helper to login a user
 */
export async function loginUser(page: Page, user: TestUser) {
  // Navigate to login page
  await page.goto('/login');

  // Fill in credentials
  await page.fill('input[name="username"], input[type="email"]', user.username);
  await page.fill('input[name="password"], input[type="password"]', user.password);

  // Submit form
  await page.click('button[type="submit"]');

  // Wait for redirect (adjust based on your app's behavior)
  await page.waitForURL(/\/(dashboard|listings|collections)/, { timeout: 10000 });
}

/**
 * Helper to logout user
 */
export async function logoutUser(page: Page) {
  // Click user menu or logout button (adjust selector based on your app)
  const logoutButton = page.locator('button:has-text("Logout"), button:has-text("Sign out")');
  if (await logoutButton.isVisible({ timeout: 2000 }).catch(() => false)) {
    await logoutButton.click();
  } else {
    // Alternative: clear cookies and local storage
    await page.context().clearCookies();
    await page.evaluate(() => localStorage.clear());
  }

  await page.goto('/');
}

/**
 * Helper to check if element is visible with retry
 */
export async function waitForVisible(
  page: Page,
  selector: string,
  timeout: number = 5000
): Promise<boolean> {
  try {
    await page.waitForSelector(selector, { state: 'visible', timeout });
    return true;
  } catch {
    return false;
  }
}

/**
 * Helper to verify toast notification appears
 */
export async function verifyToast(
  page: Page,
  expectedText: string | RegExp,
  timeout: number = 5000
) {
  const toast = page.locator('[role="status"], [data-sonner-toast], .toast, [data-toast]');
  await expect(toast.filter({ hasText: expectedText })).toBeVisible({ timeout });
}

/**
 * Helper to get share link from Share Modal
 */
export async function getShareLink(page: Page): Promise<string> {
  const input = page.locator('input#share-link');
  await expect(input).toBeVisible({ timeout: 5000 });
  const value = await input.inputValue();
  expect(value).toMatch(/^http/);
  return value;
}

/**
 * Helper to verify mobile touch target size
 */
export async function verifyTouchTargetSize(
  page: Page,
  selector: string,
  minSize: number = 44
) {
  const element = page.locator(selector);
  const box = await element.boundingBox();

  if (!box) {
    throw new Error(`Element ${selector} not found or has no bounding box`);
  }

  expect(box.width).toBeGreaterThanOrEqual(minSize);
  expect(box.height).toBeGreaterThanOrEqual(minSize);
}

/**
 * Helper to simulate clipboard copy on different browsers
 */
export async function copyToClipboard(page: Page): Promise<string> {
  // Grant clipboard permissions
  await page.context().grantPermissions(['clipboard-read', 'clipboard-write']);

  // Get clipboard text
  const clipboardText = await page.evaluate(() => navigator.clipboard.readText());
  return clipboardText;
}

/**
 * Helper to create a test collection
 */
export async function createCollection(
  page: Page,
  name: string,
  description?: string
): Promise<void> {
  // Click "New Collection" button
  await page.click('button:has-text("New collection"), button:has-text("New Collection")');

  // Wait for form to appear
  await page.waitForSelector('input[name="name"], input[id="collection-name"]', {
    state: 'visible',
    timeout: 5000
  });

  // Fill in form
  await page.fill('input[name="name"], input[id="collection-name"]', name);

  if (description) {
    await page.fill(
      'textarea[name="description"], textarea[id="collection-description"]',
      description
    );
  }

  // Submit
  await page.click('button[type="submit"]:has-text("Create"), button:has-text("Create")');

  // Wait for success (redirect or toast)
  await Promise.race([
    page.waitForURL(/\/collections\/\d+/, { timeout: 10000 }),
    verifyToast(page, /created/i, 10000),
  ]);
}

/**
 * Helper to add item to collection from listing page
 */
export async function addToCollection(
  page: Page,
  collectionName: string
): Promise<void> {
  // Click "Add to Collection" button
  await page.click('button:has-text("Add to Collection")');

  // Wait for collection selector
  await page.waitForSelector('[role="dialog"], [data-radix-collection-content]', {
    state: 'visible',
    timeout: 5000,
  });

  // Select collection
  await page.click(`button:has-text("${collectionName}"), [role="option"]:has-text("${collectionName}")`);

  // Verify success
  await verifyToast(page, /added/i);
}

/**
 * Helper to delete a collection
 */
export async function deleteCollection(page: Page): Promise<void> {
  // Click delete button (adjust selector based on your UI)
  await page.click('button[aria-label*="Delete"], button:has-text("Delete")');

  // Confirm deletion
  await page.click('button:has-text("Confirm"), button:has-text("Delete")');

  // Wait for success
  await verifyToast(page, /deleted/i);
}

/**
 * Helper to export collection data
 */
export async function exportCollection(
  page: Page,
  format: 'csv' | 'json' = 'csv'
): Promise<void> {
  // Set up download listener
  const downloadPromise = page.waitForEvent('download');

  // Click export button
  await page.click(`button:has-text("Export")`);

  // If there's a format selector, choose format
  const formatButton = page.locator(`button:has-text("${format.toUpperCase()}")`);
  if (await formatButton.isVisible({ timeout: 1000 }).catch(() => false)) {
    await formatButton.click();
  }

  // Wait for download to start
  const download = await downloadPromise;

  // Verify filename
  const filename = download.suggestedFilename();
  expect(filename).toMatch(new RegExp(`\\.${format}$`, 'i'));
}
