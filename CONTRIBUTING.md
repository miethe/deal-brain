# Contributing to Deal Brain

Thank you for your interest in contributing to Deal Brain! This document provides guidelines and instructions for contributing to the project. Whether you're fixing bugs, adding features, or improving documentation, we appreciate your help.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Standards](#code-standards)
- [Pull Request Process](#pull-request-process)
- [Commit Message Convention](#commit-message-convention)
- [Testing Requirements](#testing-requirements)
- [Issue Reporting](#issue-reporting)
- [Code of Conduct](#code-of-conduct)

## Getting Started

### Fork and Clone

1. **Fork the repository** on GitHub by clicking the "Fork" button
2. **Clone your fork locally:**
   ```bash
   git clone https://github.com/your-username/deal-brain.git
   cd deal-brain
   ```
3. **Add upstream remote** to sync with the main repository:
   ```bash
   git remote add upstream https://github.com/miethe/deal-brain.git
   ```
4. **Create a feature branch** from `main`:
   ```bash
   git fetch upstream
   git checkout -b feat/your-feature-name upstream/main
   ```

### Branch Naming Convention

Use descriptive branch names following this pattern:
- `feat/feature-name` - New feature
- `fix/bug-description` - Bug fix
- `docs/documentation-topic` - Documentation updates
- `refactor/component-name` - Code refactoring
- `test/test-description` - Tests only
- `chore/task-name` - Build, CI, or maintenance tasks

Example: `feat/add-bulk-import-support`, `fix/cpu-benchmark-calculation`

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+ and pnpm
- PostgreSQL 14+ (for database work)
- Docker and Docker Compose (for full stack)

### Local Environment Setup

1. **Install dependencies:**
   ```bash
   make setup
   ```
   This runs:
   - `poetry install` for Python dependencies
   - `pnpm install --frozen-lockfile=false` for JavaScript dependencies

2. **Set up environment variables:**
   ```bash
   # Copy example configuration
   cp .env.example .env

   # Edit .env with your local settings
   # Default values work for local development
   ```

3. **Run database migrations:**
   ```bash
   make migrate
   ```

4. **Seed sample data (optional):**
   ```bash
   make seed
   ```

### Running Services

**Option 1: Full Docker Stack** (recommended for testing)
```bash
make up          # Start all services (API, web, database, Redis, etc.)
make down        # Stop all services
```

Services available at:
- API: http://localhost:8020 (or http://localhost:8000 if running locally)
- Web UI: http://localhost:3020
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3021 (admin/admin)

**Option 2: Run Locally** (recommended for development)
```bash
# Terminal 1: Start FastAPI backend
make api

# Terminal 2: Start Next.js frontend
make web

# The frontend automatically connects to http://localhost:8000
```

### Verify Setup

After setup, verify everything works:

```bash
# Run all tests
make test

# Lint code
make lint

# Format code
make format
```

If all commands pass, your environment is ready!

## Code Standards

Maintain code quality by following these standards. All commits should pass linting and formatting.

### Python Code Style

**Tools:** Black (formatter), isort (import sorting), Ruff (linter)

**Key Rules:**
- Line length: 100 characters
- Import sorting: Black profile with isort
- No unused imports (enforced by Ruff)
- Use type hints for function parameters and returns
- Follow PEP 8 conventions

**Before committing Python code:**
```bash
# Format code
poetry run black .
poetry run isort .

# Lint and check
poetry run ruff check .
```

Or use the convenience command:
```bash
make format  # Runs black and isort for Python, prettier for TypeScript
make lint    # Runs ruff for Python, eslint for TypeScript
```

**Type Checking:**
```bash
poetry run mypy apps/api apps/cli packages/core
```

**Code Style Example:**
```python
# ✅ Good
def calculate_valuation(
    listing: Listing, rules: List[ValuationRule]
) -> ValuationResult:
    """Calculate adjusted valuation for a listing.

    Args:
        listing: The listing to valuate
        rules: Valuation rules to apply

    Returns:
        ValuationResult with breakdown
    """
    adjustments = [rule.apply(listing) for rule in rules]
    return apply_adjustments(listing, adjustments)


# ❌ Avoid
def calc_val(listing, rules):  # Too short, missing types
    # Calculate valuation
    adj = []
    for r in rules:
        adj.append(r.apply(listing))
    return apply_adjustments(listing, adj)
```

### TypeScript/JavaScript Code Style

**Tools:** ESLint, Prettier

**Key Rules:**
- Use TypeScript for type safety
- Follow ESLint configuration in `apps/web/`
- Format with Prettier
- No `console.log()` in production code (use proper logging)
- Use React best practices (functional components, hooks)

**Before committing TypeScript code:**
```bash
# Format and lint
pnpm --filter web lint --fix

# Type check
pnpm --filter web tsc --noEmit
```

**Code Style Example:**
```typescript
// ✅ Good
interface ListingProps {
  listingId: string;
  onUpdate?: (listing: Listing) => void;
}

export function ListingCard({ listingId, onUpdate }: ListingProps) {
  const { data: listing } = useQuery({
    queryKey: ['listing', listingId],
    queryFn: () => fetchListing(listingId)
  });

  return (
    <div className="listing-card">
      {listing && <ListingDetails listing={listing} />}
    </div>
  );
}


// ❌ Avoid
export function ListingCard(props) {  // Missing types
  const listing = useQuery(...);
  console.log('Rendering listing', props.listingId);  // No console.log
  return <div>{listing && <ListingDetails listing={listing} />}</div>;
}
```

### Documentation Style

- Use clear, concise language
- Include code examples for complex features
- Add docstrings to all public functions
- Update README.md if you change user-facing features
- Reference related documentation

**Docstring Example:**
```python
def import_excel_workbook(
    file_path: str, force_recalculate: bool = False
) -> ImportJob:
    """Import listings from Excel workbook.

    Parses workbook, deduplicates against existing listings, and upserts
    data through the import pipeline. Automatically calculates metrics
    and applies valuation rules.

    Args:
        file_path: Path to Excel workbook
        force_recalculate: If True, recalculate all metrics even for
                          existing listings

    Returns:
        ImportJob with completion status and summary

    Raises:
        FileNotFoundError: If workbook doesn't exist
        ValueError: If workbook format is invalid

    Example:
        >>> job = import_excel_workbook('listings.xlsx')
        >>> print(f'Imported {job.total_rows} rows')
    """
    # Implementation
```

### No Debug Code in Production

Remove all temporary debugging before committing:

**Remove these:**
```python
print("Debug value:", x)          # ❌ No print statements
import pdb; pdb.set_trace()       # ❌ No debuggers
logger.debug("temp debug")         # ❌ Only use in real debugging
```

**Use proper logging instead:**
```python
from loguru import logger

logger.info("Processing listing", listing_id=listing_id)
logger.error("Failed to import", error=str(e), file_path=file_path)
```

**For TypeScript/JavaScript:**
```typescript
console.log("debug")              // ❌ No console.log
console.error("error")            // ⚠️ Only for errors
```

## Pull Request Process

### Before Creating a PR

1. **Ensure tests pass:**
   ```bash
   make test
   ```

2. **Format and lint code:**
   ```bash
   make format && make lint
   ```

3. **Update documentation:**
   - Add comments to complex code
   - Update relevant docs if behavior changes
   - Update CHANGELOG.md if it exists

4. **Create focused commits** using proper message format (see below)

5. **Sync with upstream:**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

### Creating the Pull Request

1. **Push to your fork:**
   ```bash
   git push origin feat/your-feature-name
   ```

2. **Create PR on GitHub** with a clear description:
   - Start with issue number if fixing an issue: `Fixes #123`
   - Explain what changes were made and why
   - Describe how to test the changes
   - List any breaking changes
   - Reference related issues or PRs

3. **Example PR Description:**
   ```markdown
   ## Description
   Implements bulk import from CSV files, allowing users to upload multiple
   listings at once with automatic deduplication.

   Fixes #456

   ## Changes
   - Added CSV parser in `apps/api/dealbrain_api/importers/csv.py`
   - Created `/api/v1/imports/bulk` endpoint
   - Added E2E tests for bulk import flow
   - Updated documentation in `docs/guides/importing.md`

   ## Testing
   1. Navigate to Dashboard > Import
   2. Select "Bulk CSV Upload"
   3. Upload test file `examples/sample_listings.csv`
   4. Verify all 50 listings imported correctly
   5. Check for duplicates with existing listings

   ## Breaking Changes
   None

   ## Related
   - Relates to epic: #400
   - Depends on: #450
   ```

### PR Review Process

- **Code review:** At least one maintainer approval required
- **Tests:** All CI checks must pass
- **Coverage:** New code should maintain >70% test coverage
- **Documentation:** User-facing changes need documentation updates
- **Feedback:** Respond to reviewer comments promptly

### Merging

Once approved:
1. Keep commits clean (squash if needed for clarity)
2. Merge using "Squash and merge" or "Create a merge commit" (maintainer decides)
3. Delete the feature branch after merge

## Commit Message Convention

Write clear, descriptive commit messages using conventional commit format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type (required)

- **feat:** A new feature
- **fix:** A bug fix
- **docs:** Documentation updates
- **refactor:** Code refactoring without feature or bug changes
- **test:** Tests only (no production code changes)
- **chore:** Build, CI, dependency updates, etc.

### Scope (optional)

The scope specifies what part of the codebase is affected:
- `listings` - Listing-related code
- `valuation` - Valuation engine
- `rules` - Valuation rules
- `imports` - Import system
- `api` - API endpoints
- `ui` - Frontend components
- `core` - Domain logic in packages/core
- `db` - Database or migrations
- `cli` - CLI commands

### Subject (required)

- Use imperative mood: "add" not "added" or "adds"
- Don't capitalize first letter
- No period at the end
- 50 characters or less

### Body (optional but recommended)

- Explain what and why, not how
- Wrap at 72 characters
- Separate from subject with a blank line

### Footer (optional)

Reference issues and breaking changes:
- `Fixes #123` - Close associated issue
- `BREAKING CHANGE: description` - Document breaking changes

### Commit Examples

**Good commits:**
```
feat(listings): add bulk import from CSV

Implement endpoint /api/v1/imports/bulk to accept CSV file uploads
containing multiple listings. Automatically deduplicates against
existing listings using fuzzy matching on title and specs.

Fixes #456
```

```
fix(valuation): correct CPU benchmark score lookup

Use exact match for CPU part number instead of substring match
to avoid incorrect valuations when similar part numbers exist.

Fixes #678
```

```
docs(readme): update API base URL for Docker setup

Clarify that when running in Docker, frontend must use host IP
(e.g., http://10.42.9.11:8020) instead of localhost.
```

```
refactor(core): extract component adjustment logic into separate function

Move component-based pricing adjustments to dedicated function for
reusability across import and ranking services.
```

```
test(imports): add tests for CSV deduplication

Add 5 new tests covering edge cases in deduplication:
- Exact matches
- Fuzzy matches above threshold
- Unicode handling
- Empty listings
- Duplicate rows in same file
```

**Poor commits (avoid):**
```
fix bug              # Too vague
Fixed the valuation  # Not imperative mood
Updated stuff        # Unclear what changed
FEAT: BIG CHANGE     # Wrong format
```

## Testing Requirements

All pull requests must include tests. Maintain high code quality through comprehensive testing.

### Backend Testing (Python/pytest)

**Coverage Target:** >70% for new code

**Running Tests:**
```bash
# Run all tests
make test

# Run specific test file
poetry run pytest tests/test_listings_service.py -v

# Run specific test
poetry run pytest tests/test_listings_service.py::test_create_listing -v

# Run with coverage report
poetry run pytest --cov=apps/api --cov=packages/core --cov-report=html
```

**Test Structure:**
```python
def test_calculate_valuation_applies_all_rules(listing_factory, rules):
    """Test that all applicable rules are applied to valuation."""
    listing = listing_factory.create(base_price=1000)

    result = calculate_valuation(listing, rules)

    assert result.base_price == 1000
    assert len(result.adjustments) == len(rules)
    assert result.adjusted_price < result.base_price
```

**Key Guidelines:**
- Use descriptive test names: `test_<function>_<scenario>_<expected>`
- Test both happy path and error cases
- Use fixtures for common setup (see `tests/conftest.py`)
- Mock external services (APIs, databases in integration tests)
- Include docstrings explaining complex test logic
- Use factories (factory-boy) for test data

**Test Fixtures:**
```python
# Use existing fixtures from tests/conftest.py
def test_import_job_creates_listings(session_fixture, listing_factory):
    # session_fixture provides database session
    # listing_factory creates test data
    pass
```

### Frontend Testing (TypeScript/Jest and Playwright)

**Logic Tests (Jest):**
```typescript
describe('calculateValuationScore', () => {
  it('returns higher score for lower-priced items with same specs', () => {
    const item1 = { price: 100, specs: { cpu: 'i7', ram: 16 } };
    const item2 = { price: 150, specs: { cpu: 'i7', ram: 16 } };

    const score1 = calculateScore(item1);
    const score2 = calculateScore(item2);

    expect(score1).toBeGreaterThan(score2);
  });
});
```

**Component Tests (React Testing Library):**
```typescript
import { render, screen } from '@testing-library/react';
import { ListingCard } from './ListingCard';

it('displays listing details when loaded', async () => {
  render(<ListingCard listingId="123" />);

  await screen.findByText(/Loading/);

  const title = await screen.findByText(/Intel i7/);
  expect(title).toBeInTheDocument();
});
```

**E2E Tests (Playwright):**
```typescript
test('user can import CSV and view results', async ({ page }) => {
  await page.goto('/dashboard/import');
  await page.click('text=Upload CSV');
  await page.setInputFiles('input[type="file"]', 'test_data.csv');
  await page.click('text=Import');

  await expect(page.locator('text=Import complete')).toBeVisible();
});
```

**Running Frontend Tests:**
```bash
cd apps/web

# Run all tests
pnpm test

# Run with coverage
pnpm test --coverage

# Run E2E tests
pnpm e2e

# Run specific test
pnpm test calculator.test.ts
```

### Test Quality Checklist

Before submitting PR with tests:

- [ ] Tests pass locally: `make test`
- [ ] New code has >70% coverage
- [ ] Test names are descriptive
- [ ] Happy path tested
- [ ] Error cases tested
- [ ] Edge cases considered
- [ ] Tests don't depend on external services (mocked)
- [ ] Tests run in <5 minutes
- [ ] No hardcoded values (use factories/fixtures)
- [ ] No sleep/wait statements (use proper async/await)

## Issue Reporting

Found a bug or have a feature request? Help us improve by reporting issues clearly.

### Bug Report Template

**Title:** Clear, one-sentence description
Example: "Valuation breakdown modal crashes when CPU has no benchmark data"

**Description:**
```markdown
## Description
Brief description of the bug.

## Steps to Reproduce
1. Navigate to...
2. Click on...
3. Observe...

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Screenshots
(If applicable)

## Environment
- Browser: Chrome 120
- OS: macOS 14
- API URL: http://localhost:8000
- Version: main branch (commit abc123)

## Additional Context
Any other relevant information
```

### Feature Request Template

**Title:** Clear description of feature
Example: "Add ability to export valuations to CSV"

**Description:**
```markdown
## Use Case
Why is this feature needed? What problem does it solve?

## Proposed Solution
How should this feature work?

## Alternatives Considered
Any other approaches?

## Examples
Show how a user would use this feature

## Additional Context
Links to related issues, specifications, etc.
```

### Good Issue Examples

Good:
- "Import fails for listings with emoji in title"
- "Add keyboard shortcut (Ctrl+K) for search"
- "CPU benchmark scores are missing for Ryzen 7 9700X"

Avoid:
- "Something is broken"
- "Make it faster"
- "UI looks bad"

## Code of Conduct

### Our Commitment

We are committed to providing a welcoming and inclusive environment for all contributors. We expect all members of our community to be respectful and constructive.

### Expected Behavior

- Be respectful and inclusive
- Welcome diverse perspectives and backgrounds
- Focus on constructive criticism
- Be patient with others learning the codebase
- Give credit to others' contributions

### Unacceptable Behavior

The following behaviors are not acceptable:
- Harassment, discrimination, or demeaning language
- Trolling or insulting comments
- Sexual or violent content
- Spam or off-topic disruptions
- Publishing private information without consent

### Reporting Violations

If you experience or witness inappropriate behavior:
1. Document the incident
2. Report to the maintainers
3. We will investigate and respond appropriately

---

## Additional Resources

- [Development Setup Documentation](/docs/development/getting-started.md)
- [Architecture Guide](/docs/architecture/)
- [API Documentation](/docs/api/)
- [Design System](/docs/design/)
- [GitHub Issues](https://github.com/miethe/deal-brain/issues)
- [Discussions](https://github.com/miethe/deal-brain/discussions)

## Questions?

- Check existing [GitHub Issues](https://github.com/miethe/deal-brain/issues)
- Start a [Discussion](https://github.com/miethe/deal-brain/discussions)
- Review [Documentation](/docs/)

Thank you for contributing to Deal Brain!
