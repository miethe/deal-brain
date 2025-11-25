# E2E Tests

End-to-end tests for Deal Brain using Playwright.

## Quick Start

```bash
# Install dependencies
pnpm install

# Install Playwright browsers
pnpm exec playwright install

# Run all E2E tests
pnpm test:e2e

# Run specific test file
pnpm test:e2e tests/e2e/entity-crud.spec.ts

# Run tests in UI mode (interactive)
pnpm test:e2e:ui

# Run tests in headed mode (see browser)
pnpm test:e2e:headed
```

## Prerequisites

1. **Backend API** running on `http://localhost:8000`
   ```bash
   make api
   ```

2. **Frontend web server** running on `http://localhost:3020`
   ```bash
   make web
   # or let Playwright auto-start it
   ```

3. **Database** migrated and ready
   ```bash
   make migrate
   ```

## Test Files

| File | Description | Tests |
|------|-------------|-------|
| `listings.spec.ts` | Listings management tests | 7 |
| `global-fields.spec.ts` | Global fields workspace tests | 6 |
| `data-grid.spec.ts` | Data grid features tests | 8 |
| `entity-crud.spec.ts` | Entity CRUD operations tests | 14 |

**Total**: 35+ E2E tests

## Entity CRUD Tests

Comprehensive tests for entity detail pages covering:

- ✅ Edit entity specification
- ✅ Delete unused entity
- ✅ Block delete of in-use entity
- ✅ Manage entities from global fields
- ✅ Keyboard accessibility
- ✅ Mobile responsive design
- ✅ ARIA labels

See [`ENTITY_CRUD_TEST_SUMMARY.md`](./ENTITY_CRUD_TEST_SUMMARY.md) for detailed documentation.

## Running Specific Tests

### By User Story
```bash
pnpm test:e2e tests/e2e/entity-crud.spec.ts --grep "US-1"
pnpm test:e2e tests/e2e/entity-crud.spec.ts --grep "US-2"
pnpm test:e2e tests/e2e/entity-crud.spec.ts --grep "US-3"
pnpm test:e2e tests/e2e/entity-crud.spec.ts --grep "US-4"
```

### By Feature
```bash
pnpm test:e2e tests/e2e/entity-crud.spec.ts --grep "Edit"
pnpm test:e2e tests/e2e/entity-crud.spec.ts --grep "Delete"
pnpm test:e2e tests/e2e/entity-crud.spec.ts --grep "Accessibility"
```

### By Browser
```bash
pnpm test:e2e tests/e2e/entity-crud.spec.ts --project=chromium
pnpm test:e2e tests/e2e/entity-crud.spec.ts --project=webkit
```

## Debugging Tests

### Use Playwright UI Mode
```bash
pnpm test:e2e:ui tests/e2e/entity-crud.spec.ts
```

Features:
- Time-travel debugging
- Watch mode
- Step-by-step execution
- Network inspection

### Use Headed Mode
```bash
pnpm test:e2e:headed tests/e2e/entity-crud.spec.ts
```

See the browser as tests run.

### Generate Test Report
```bash
pnpm test:e2e
npx playwright show-report
```

Opens HTML report with screenshots and traces.

## Test Structure

### Example Test
```typescript
test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    // Setup: Create test data
  });

  test.afterEach(async ({ page }) => {
    // Cleanup: Delete test data
  });

  test('should do something', async ({ page }) => {
    // Arrange: Navigate to page
    await page.goto('/some-page');

    // Act: Perform action
    await page.click('button:has-text("Click Me")');

    // Assert: Verify result
    await expect(page.locator('text=Success')).toBeVisible();
  });
});
```

## Configuration

Playwright config: [`/home/user/deal-brain/playwright.config.ts`](/home/user/deal-brain/playwright.config.ts)

Key settings:
- Base URL: `http://localhost:3020`
- Timeout: 30s
- Retries: 0 (local), 2 (CI)
- Screenshots: On failure
- Trace: On first retry

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Install dependencies
  run: pnpm install

- name: Install Playwright
  run: pnpm exec playwright install --with-deps

- name: Run E2E tests
  run: pnpm test:e2e

- name: Upload test results
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: playwright-report
    path: playwright-report/
```

## Manual Testing

If automated tests cannot run, use the manual test checklist:

[`MANUAL_TEST_CHECKLIST.md`](./MANUAL_TEST_CHECKLIST.md)

## Documentation

- [`ENTITY_CRUD_TEST_SUMMARY.md`](./ENTITY_CRUD_TEST_SUMMARY.md) - Detailed test documentation
- [`MANUAL_TEST_CHECKLIST.md`](./MANUAL_TEST_CHECKLIST.md) - Manual testing guide
- [`TEST_DELIVERABLES.md`](./TEST_DELIVERABLES.md) - Deliverables summary

## Troubleshooting

### Tests fail at navigation
- Ensure backend is running on port 8000
- Ensure frontend is running on port 3020
- Check that routes exist

### Tests timeout
- Increase timeout in playwright.config.ts
- Check for slow API responses
- Verify database is seeded

### Modal doesn't open
- Check button selectors
- Verify modal component is mounted
- Look for console errors

### Toast doesn't appear
- Adjust timeout (toasts may be slow)
- Check toast selector
- Verify mutation succeeded

## Best Practices

1. **Test Independence**: Each test should be independent
2. **Cleanup**: Always clean up test data
3. **Selectors**: Use semantic selectors (text, role, label)
4. **Assertions**: Be specific about what you're testing
5. **Timeouts**: Use reasonable timeouts, not arbitrary waits

## Support

For issues or questions:
1. Check test output and screenshots
2. Review browser console logs
3. Check Playwright docs: https://playwright.dev/
4. Review existing tests for patterns

---

**Framework**: Playwright v1.40.0
**Total Tests**: 35+
**Last Updated**: 2025-11-14
