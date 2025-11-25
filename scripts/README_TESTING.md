# Testing Scripts

This directory contains testing and quality assurance scripts for the Deal Brain project.

## Security Audit

**File:** `security_audit.py`

Comprehensive security testing for the Collections Sharing feature.

### Tests Performed

1. **Token Security**
   - Token length validation (64 characters)
   - Token format validation (URL-safe characters)
   - Token uniqueness and randomness
   - Token guessing resistance (brute force)

2. **SQL Injection Prevention**
   - Collection name/description injection attempts
   - Parameter injection in API endpoints
   - Query parameter validation
   - ORM parameterization verification

3. **XSS Prevention**
   - Script injection in user inputs
   - HTML tag injection
   - Event handler injection
   - URL injection

4. **CSRF Protection**
   - Authentication requirement for mutations
   - CORS header configuration
   - Session token validation

5. **Rate Limiting**
   - Share creation rate limit (10/hour) enforcement
   - Read operation exemption from rate limits
   - Error message information leakage prevention

6. **Authorization**
   - Collection ownership validation
   - Cross-user access prevention
   - Non-existent resource handling
   - Production auth readiness check

### Usage

```bash
# Install dependencies (if not already installed)
poetry install

# Run security audit
poetry run python scripts/security_audit.py

# View report
cat docs/testing/security-audit-report.md
```

### Output

- Console output with colored test results
- Detailed markdown report: `docs/testing/security-audit-report.md`
- Exit code 0 on success, 1 if critical failures detected

### Requirements

- API server running on `http://localhost:8000`
- Database with test data seeded
- Redis available (for caching tests)

## Load Testing

**File:** `load_test.py`

Performance and scalability testing for the Collections Sharing feature.

### Tests Performed

1. **Collections Endpoint Load Test**
   - 100 concurrent users
   - Collections with 100+ items
   - Target: p95 < 200ms

2. **Public Share Pages Load Test**
   - 500 concurrent requests (uncached)
   - 500 concurrent requests (cached)
   - Target: p95 < 1s (uncached), p95 < 50ms (cached)

3. **Share Creation Load Test**
   - 50 concurrent users creating shares
   - Rate limiting verification under load
   - Target: p95 < 500ms

4. **Database Connection Pool Test**
   - 200 concurrent database queries
   - Connection leak detection
   - Max connection monitoring
   - Target: No pool exhaustion, p95 < 300ms

### Usage

```bash
# Install dependencies (if not already installed)
poetry install

# Seed test data first
poetry run python scripts/seed_test_data.py

# Run load tests
poetry run python scripts/load_test.py

# View report
cat docs/testing/performance-load-test-report.md
```

### Output

- Console output with performance metrics
- Detailed markdown report: `docs/testing/performance-load-test-report.md`
- Metrics include:
  - p50, p95, p99 response times
  - Min, max, average response times
  - Throughput (requests/second)
  - Success/failure counts
  - Error details

### Requirements

- API server running on `http://localhost:8000`
- Database with adequate test data
  - At least 100 listings for collection tests
  - At least 2 users for sharing tests
- Redis available (for caching tests)
- PostgreSQL with adequate connection pool size

### Performance Targets

| Test | Target p95 | Description |
|------|-----------|-------------|
| Collections (100+ items) | < 200ms | 100 concurrent users |
| Public share (uncached) | < 1s | 500 concurrent requests |
| Public share (cached) | < 50ms | 500 concurrent requests |
| Share creation | < 500ms | 50 concurrent users |
| Connection pool | < 300ms | 200 concurrent queries |

## Test Data Setup

Before running tests, ensure test data is seeded:

```bash
# Seed comprehensive test data
poetry run python scripts/seed_test_data.py

# Or use the existing seed script
make seed
```

Required test data:
- At least 2 users (user_id 1 and 2)
- At least 100 listings with complete data
- CPU and GPU catalog data
- Application settings configured

## Troubleshooting

### Security Audit Issues

**Problem:** "Failed to create test collection"
- **Solution:** Ensure API is running and database is accessible

**Problem:** "PLACEHOLDER AUTH IN USE" warning
- **Solution:** This is expected during development. Replace with JWT auth before production.

**Problem:** Rate limiting tests failing
- **Solution:** Wait 1 hour between test runs to reset rate limits, or clear Redis cache

### Load Test Issues

**Problem:** "Connection pool exhausted"
- **Solution:** Increase PostgreSQL `max_connections` or decrease test concurrency

**Problem:** High p95 response times
- **Solution:** Check database query performance, ensure indexes are created

**Problem:** "Failed to create test collection with items"
- **Solution:** Ensure at least 100 listings exist in database

## CI/CD Integration

These scripts can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Security Audit
  run: poetry run python scripts/security_audit.py

- name: Run Load Tests
  run: poetry run python scripts/load_test.py

- name: Upload Reports
  uses: actions/upload-artifact@v3
  with:
    name: test-reports
    path: docs/testing/*.md
```

## Dependencies

All dependencies are managed via Poetry:

```toml
# pyproject.toml
[tool.poetry.group.dev.dependencies]
colorama = "^0.4.6"  # Colored terminal output

[tool.poetry.dependencies]
httpx = "^0.26.0"     # HTTP client for API testing
```

## Contributing

When adding new security or performance tests:

1. Follow existing test patterns
2. Add descriptive test names and documentation
3. Include severity levels for security tests
4. Set realistic performance targets
5. Update this README with new test descriptions
6. Generate sample reports for documentation

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [Web Performance Best Practices](https://web.dev/performance/)
