# E2E Test Suite Guide

Comprehensive end-to-end tests for Deal Brain critical user flows.

## Test Suites

### 1. Share & Public Page Flow (`share-public-page.spec.ts`)

Tests the complete flow of sharing a listing via public link:
- Share link generation (<500ms)
- Copy to clipboard functionality
- Public deal page rendering (<1s load time)
- OpenGraph meta tags verification
- Add to collection from public page
- Expired link handling

**Run:**
```bash
pnpm test:e2e:share
# or
npx playwright test tests/e2e/share-public-page.spec.ts
```

### 2. User-to-User Share Flow (`user-to-user-share.spec.ts`)

Tests direct sharing between users:
- User search with debouncing (200ms)
- Share with message
- Notification delivery
- Import to collection with metadata preservation
- Rate limiting (10 shares/hour)
- Email notification trigger

**Run:**
```bash
pnpm test:e2e:share
# or
npx playwright test tests/e2e/user-to-user-share.spec.ts
```

### 3. Collections Workflow (`collections-workflow.spec.ts`)

Tests complete collection management:
- Collection creation (<500ms)
- Item addition from listings
- Notes editing with auto-save (500ms debounce)
- Status management
- Filtering and sorting
- View switching (table/card)
- CSV export
- Collection deletion with cascade

**Run:**
```bash
pnpm test:e2e:collections
# or
npx playwright test tests/e2e/collections-workflow.spec.ts
```

### 4. Mobile Flows (`mobile-flows.spec.ts`)

Tests mobile-specific interactions:
- Touch target sizes (≥44px)
- Responsive layouts
- Modal fit to viewport
- Mobile keyboard interactions
- Collapsible filters
- Swipe gestures (if implemented)
- Cross-device compatibility

**Run:**
```bash
pnpm test:e2e:mobile
# or
npx playwright test tests/e2e/mobile-flows.spec.ts
```

## Quick Start

### Prerequisites

1. **Install dependencies:**
   ```bash
   pnpm install
   npx playwright install
   ```

2. **Seed test data:**
   ```bash
   # Create test users and listings
   make seed
   # or
   poetry run python scripts/seed_test_data.py
   ```

3. **Start services:**
   ```bash
   # Start API and web server
   make up
   # or
   pnpm web # in one terminal
   # API should be running on port 8020
   ```

### Running Tests

**Run all E2E tests:**
```bash
pnpm test:e2e
```

**Run critical flows only:**
```bash
pnpm test:e2e:critical
```

**Run in UI mode (interactive):**
```bash
pnpm test:e2e:ui
```

**Run in headed mode (see browser):**
```bash
pnpm test:e2e:headed
```

**Run specific test file:**
```bash
npx playwright test tests/e2e/share-public-page.spec.ts
```

**Run specific test:**
```bash
npx playwright test tests/e2e/share-public-page.spec.ts -g "should copy share link"
```

**View test report:**
```bash
pnpm test:e2e:report
# or
npx playwright show-report
```

## Test Data Requirements

These tests require seeded data:

1. **Test Users:**
   - `testuser_a` (usera@test.com)
   - `testuser_b` (userb@test.com)

2. **Test Listings:**
   - At least 10 listings with various CPUs, prices, and specs

3. **Test Collections:**
   - Some tests create collections dynamically
   - Others may require existing collections

**Seed script example:**
```python
# scripts/seed_test_data.py
from dealbrain_api.services.users import create_user
from dealbrain_api.services.listings import create_listing

# Create test users
user_a = create_user(username="testuser_a", email="usera@test.com", password="testpass123")
user_b = create_user(username="testuser_b", email="userb@test.com", password="testpass123")

# Create test listings
# ... (see existing seed scripts)
```

## Configuration

### Playwright Config (`/home/user/deal-brain/playwright.config.ts`)

```typescript
export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3020',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  ],
  webServer: {
    command: 'pnpm --filter web dev',
    url: 'http://localhost:3020',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
```

### Environment Variables

Set these in `.env` or CI environment:

```bash
# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8020

# Backend (for seeding)
DATABASE_URL=postgresql://user:pass@localhost:5442/dealbrain
```

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/e2e-tests.yml
name: E2E Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  e2e:
    runs-on: ubuntu-latest
    timeout-minutes: 15

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: dealbrain_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5442:5432

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6399:6379

    steps:
      - uses: actions/checkout@v3

      - uses: pnpm/action-setup@v2
        with:
          version: 8

      - uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'pnpm'

      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pnpm install --frozen-lockfile
          poetry install

      - name: Install Playwright browsers
        run: npx playwright install --with-deps

      - name: Setup database
        run: |
          poetry run alembic upgrade head
          poetry run python scripts/seed_test_data.py

      - name: Start API server
        run: |
          poetry run uvicorn dealbrain_api.main:app --host 0.0.0.0 --port 8020 &
          sleep 5

      - name: Run E2E tests
        run: pnpm test:e2e:critical

      - name: Upload test report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 30
```

## Debugging Tests

### Debug Mode

Run tests with Playwright Inspector:
```bash
PWDEBUG=1 npx playwright test tests/e2e/share-public-page.spec.ts
```

### Headed Mode

See the browser while tests run:
```bash
npx playwright test --headed
```

### Trace Viewer

Generate and view traces:
```bash
# Run with trace
npx playwright test --trace on

# View trace
npx playwright show-trace trace.zip
```

### Screenshots

Screenshots are automatically captured on failure and saved to `test-results/`.

### Video Recording

Enable video recording in `playwright.config.ts`:
```typescript
use: {
  video: 'retain-on-failure',
}
```

## Performance Assertions

Tests include performance checks:

- **Share link generation:** <500ms
- **Public page load:** <1s
- **Collection creation:** <500ms
- **User search debounce:** 200ms
- **Auto-save debounce:** 500ms

These thresholds ensure fast user experience.

## Accessibility

Mobile tests verify:
- Touch targets ≥ 44px (WCAG 2.1 Level AAA)
- Readable font sizes ≥ 14px
- Viewport allows user zoom
- Keyboard navigation support

## Test Maintenance

### Adding New Tests

1. Create spec file in `tests/e2e/`
2. Import helpers from `fixtures.ts`
3. Use descriptive test names
4. Include performance assertions
5. Test both happy and error paths

### Updating Fixtures

Edit `tests/e2e/fixtures.ts` to add reusable helpers.

### Flaky Tests

If tests are flaky:
1. Increase timeouts (not ideal, find root cause)
2. Add explicit waits for async operations
3. Use `waitForLoadState('networkidle')`
4. Check for race conditions

## Best Practices

1. **Deterministic tests:** No random data, use seeded data
2. **Isolated tests:** Each test should be independent
3. **Fast feedback:** Parallelize when possible
4. **Clear failures:** Descriptive error messages
5. **Minimal mocking:** Test real integrations when feasible
6. **Accessibility:** Include a11y checks in tests

## Troubleshooting

### Tests fail with "baseURL not available"

Ensure web server is running:
```bash
pnpm web
```

Or let Playwright start it automatically (default config).

### Tests fail with "API not responding"

Ensure API server is running:
```bash
make api
# or
poetry run uvicorn dealbrain_api.main:app --port 8020
```

### Database seeding issues

Reset database and reseed:
```bash
poetry run alembic downgrade base
poetry run alembic upgrade head
poetry run python scripts/seed_test_data.py
```

### Browser not installed

Install Playwright browsers:
```bash
npx playwright install
```

## Coverage Goals

Target coverage for critical flows:
- ✅ Share link generation and viewing
- ✅ User-to-user sharing with notifications
- ✅ Collection creation and management
- ✅ Item notes and status editing
- ✅ Filtering and sorting
- ✅ Export functionality
- ✅ Mobile responsive behavior
- ✅ Touch target accessibility

## Contact

For issues or questions about E2E tests, see:
- `/tests/e2e/README.md` (this file)
- Playwright docs: https://playwright.dev
- Project CLAUDE.md for development guidelines
