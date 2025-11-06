# Environment Variables Reference

Comprehensive reference for all environment variables used in Deal Brain deployment.

## Quick Start

Copy `.env.example` to `.env` and update with your values:

```bash
cp .env.example .env
nano .env
```

## Variable Categories

### Database Configuration

#### `DATABASE_URL`

Async SQLAlchemy database URL for the API.

- **Format**: `postgresql+asyncpg://user:password@host:port/database`
- **Example**: `postgresql+asyncpg://dealbrain:mypassword@db:5432/dealbrain`
- **Default**: `postgresql+asyncpg://dealbrain:dealbrain@db:5432/dealbrain`
- **Required**: Yes
- **Notes**:
  - Use `asyncpg` driver (async)
  - Change password from default in production
  - Use strong password (20+ characters)
  - For remote database, use FQDN or IP

#### `SYNC_DATABASE_URL`

Synchronous SQLAlchemy database URL for migrations and CLI tools.

- **Format**: `postgresql+psycopg://user:password@host:port/database`
- **Example**: `postgresql+psycopg://dealbrain:mypassword@db:5432/dealbrain`
- **Default**: `postgresql+psycopg://dealbrain:dealbrain@db:5432/dealbrain`
- **Required**: Yes
- **Notes**:
  - Use `psycopg` driver (synchronous)
  - Same credentials as `DATABASE_URL`
  - Used for Alembic migrations

### Redis Configuration

#### `REDIS_URL`

Redis connection URL for caching and task queue.

- **Format**: `redis://[:password@]host:port/database`
- **Example**: `redis://redis:6379/0`
- **Default**: `redis://redis:6379/0`
- **Required**: Yes
- **Notes**:
  - Database number: 0 (default)
  - Add authentication if Redis requires password
  - Use 6379 as default port

### Security Configuration

#### `SECRET_KEY`

Secret key for session management and token signing.

- **Format**: Any string (minimum 32 characters recommended)
- **Example**: `YourSuperSecureRandomKeyHere1234567890`
- **Default**: `changeme`
- **Required**: Yes
- **Security**: CRITICAL - Change in production!
- **Generation**:
  ```bash
  # Generate secure key
  python3 -c "import secrets; print(secrets.token_urlsafe(32))"
  ```

### Application Configuration

#### `ENVIRONMENT`

Deployment environment identifier.

- **Values**: `development`, `staging`, `production`
- **Default**: `development`
- **Required**: Yes
- **Effects**:
  - `production`: Stricter validation, no debug endpoints
  - `development`: Debug features enabled
  - `staging`: Same as production with some monitoring relaxed

#### `LOG_LEVEL`

Application logging verbosity.

- **Values**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Default**: `INFO`
- **Recommended**:
  - Development: `DEBUG`
  - Staging: `INFO`
  - Production: `WARNING` or `INFO`
- **Notes**: Higher levels reduce logging volume

#### `API_HOST`

Host the FastAPI server binds to.

- **Values**: `0.0.0.0`, `127.0.0.1`, or specific IP
- **Default**: `0.0.0.0`
- **Recommended**: `0.0.0.0` (allows Docker networking)
- **Notes**:
  - `0.0.0.0` = listen on all interfaces
  - `127.0.0.1` = localhost only

#### `API_PORT`

Port the FastAPI server listens on.

- **Values**: 1024-65535
- **Default**: `8000`
- **Recommended**: `8000`
- **Notes**: Must match Docker port mapping

#### `WEB_URL`

Base URL for the web application (used in emails, etc.).

- **Format**: Full URL with protocol
- **Example**: `https://yourdomain.com`
- **Default**: `http://localhost:3000`
- **Required**: For production
- **Notes**: Must include https:// in production

### Data Paths

#### `IMPORT_ROOT`

Directory path for Excel workbook imports.

- **Format**: Absolute or relative path
- **Example**: `./data/imports`
- **Default**: `./data/imports`
- **Required**: Yes
- **Notes**: Directory must exist and be writable

#### `EXPORT_ROOT`

Directory path for JSON exports.

- **Format**: Absolute or relative path
- **Example**: `./data/exports`
- **Default**: `./data/exports`
- **Required**: Yes
- **Notes**: Directory must exist and be writable

### Observability Configuration

#### `OTEL_EXPORTER_OTLP_ENDPOINT`

OpenTelemetry Collector endpoint for traces and metrics.

- **Format**: `http://host:port`
- **Example**: `http://otel-collector:4317`
- **Default**: `http://otel-collector:4317`
- **Required**: If OpenTelemetry is enabled
- **Notes**:
  - Docker: Use service name
  - External: Use IP/hostname:port

#### `PROMETHEUS_ENABLED`

Enable Prometheus metrics export.

- **Values**: `true`, `false`
- **Default**: `true`
- **Required**: No
- **Notes**: Metrics available at `/metrics` endpoint

### URL Ingestion Configuration

#### `INGESTION_INGESTION_ENABLED`

Master control for URL ingestion feature.

- **Values**: `true`, `false`
- **Default**: `true`
- **Required**: No
- **Notes**: Disables entire ingestion system when false

#### `INGESTION_EBAY_ENABLED`

Enable eBay URL ingestion adapter.

- **Values**: `true`, `false`
- **Default**: `true`
- **Required**: No
- **Depends on**: `EBAY_API_KEY`

#### `EBAY_API_KEY`

eBay API credentials for product data extraction.

- **Format**: Your eBay API key
- **Example**: `abc123def456...`
- **Default**: Empty
- **Required**: Only if `INGESTION_EBAY_ENABLED=true`
- **Security**: Keep confidential, use environment variable
- **Notes**: Obtain from eBay developer portal

#### `INGESTION_EBAY_TIMEOUT_S`

Timeout for eBay API requests in seconds.

- **Values**: Integer, 1-30
- **Default**: `6`
- **Recommended**: 6-10
- **Notes**: Longer timeout = more reliable but slower

#### `INGESTION_EBAY_RETRIES`

Number of retries for failed eBay API requests.

- **Values**: Integer, 0-5
- **Default**: `2`
- **Recommended**: 2-3
- **Notes**: Higher retries = more resilient but slower

#### `INGESTION_JSONLD_ENABLED`

Enable JSON-LD adapter (structured data extraction).

- **Values**: `true`, `false`
- **Default**: `true`
- **Required**: No
- **Notes**: No API key required, uses page structure data

#### `INGESTION_JSONLD_TIMEOUT_S`

Timeout for JSON-LD extraction in seconds.

- **Values**: Integer, 1-30
- **Default**: `8`
- **Recommended**: 8-15
- **Notes**: Web page parsing timeout

#### `INGESTION_JSONLD_RETRIES`

Number of retries for failed JSON-LD extraction.

- **Values**: Integer, 0-5
- **Default**: `1`
- **Recommended**: 1-2

#### `INGESTION_AMAZON_ENABLED`

Enable Amazon URL ingestion adapter.

- **Values**: `true`, `false`
- **Default**: `false`
- **Notes**: Not yet implemented (Phase 2 feature)

#### `AMAZON_API_KEY`

Amazon API credentials.

- **Default**: Empty
- **Required**: Only if/when Amazon adapter is enabled
- **Status**: Reserved for future implementation

#### `INGESTION_AMAZON_TIMEOUT_S`

Timeout for Amazon API requests.

- **Default**: `8`

#### `INGESTION_AMAZON_RETRIES`

Retries for Amazon API requests.

- **Default**: `1`

### Price Change Detection

#### `INGESTION_PRICE_CHANGE_THRESHOLD_PCT`

Percentage threshold to trigger price change alert.

- **Values**: 0.0-100.0 (percentage)
- **Default**: `2.0`
- **Example**: Price changes more than 2% will be flagged
- **Unit**: Percent of original price

#### `INGESTION_PRICE_CHANGE_THRESHOLD_ABS`

Absolute dollar threshold to trigger price change alert.

- **Values**: Decimal amount (USD)
- **Default**: `1.0`
- **Example**: Price changes more than $1.00 will be flagged
- **Unit**: US Dollars

### Raw Payload Management

#### `INGESTION_RAW_PAYLOAD_TTL_DAYS`

Time-to-live for raw ingestion payloads in days.

- **Values**: 1-365
- **Default**: `30`
- **Recommended**: 30-90 days
- **Notes**:
  - Payloads older than this are deleted
  - Keep for debugging and audit
  - Set lower to reduce disk usage

#### `INGESTION_RAW_PAYLOAD_MAX_BYTES`

Maximum size of raw payload to store.

- **Values**: 1024-10485760 (1KB-10MB)
- **Default**: `524288` (512KB)
- **Recommended**: 256KB-1MB
- **Notes**:
  - Prevents storing huge payloads
  - Reduces database bloat
  - Lower values = less storage needed

## Environment Variable Examples

### Development Configuration

```bash
ENVIRONMENT=development
LOG_LEVEL=DEBUG
SECRET_KEY=dev-key-not-secure-only-for-development
DATABASE_URL=postgresql+asyncpg://dealbrain:dealbrain@localhost:5432/dealbrain
SYNC_DATABASE_URL=postgresql+psycopg://dealbrain:dealbrain@localhost:5432/dealbrain
REDIS_URL=redis://localhost:6379/0
WEB_URL=http://localhost:3000
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
PROMETHEUS_ENABLED=true
INGESTION_INGESTION_ENABLED=true
INGESTION_EBAY_ENABLED=false
INGESTION_JSONLD_ENABLED=true
```

### Staging Configuration

```bash
ENVIRONMENT=staging
LOG_LEVEL=INFO
SECRET_KEY=your-secure-staging-key-min-32-chars-12345678
DATABASE_URL=postgresql+asyncpg://dealbrain:strong_password@db-staging.yourcompany.com:5432/dealbrain
SYNC_DATABASE_URL=postgresql+psycopg://dealbrain:strong_password@db-staging.yourcompany.com:5432/dealbrain
REDIS_URL=redis://redis-staging.yourcompany.com:6379/0
WEB_URL=https://staging.yourdomain.com
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector-staging:4317
PROMETHEUS_ENABLED=true
INGESTION_INGESTION_ENABLED=true
INGESTION_EBAY_ENABLED=true
EBAY_API_KEY=your-ebay-api-key
INGESTION_JSONLD_ENABLED=true
```

### Production Configuration

```bash
ENVIRONMENT=production
LOG_LEVEL=WARNING
SECRET_KEY=your-super-secure-production-key-min-32-chars-generated-randomly
DATABASE_URL=postgresql+asyncpg://dealbrain:extremely_strong_random_password@db-prod.yourcompany.com:5432/dealbrain
SYNC_DATABASE_URL=postgresql+psycopg://dealbrain:extremely_strong_random_password@db-prod.yourcompany.com:5432/dealbrain
REDIS_URL=redis://:redis_password@redis-prod.yourcompany.com:6379/0
WEB_URL=https://yourdomain.com
API_HOST=0.0.0.0
API_PORT=8000
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
PROMETHEUS_ENABLED=true
INGESTION_INGESTION_ENABLED=true
INGESTION_EBAY_ENABLED=true
EBAY_API_KEY=your-production-ebay-api-key
INGESTION_JSONLD_ENABLED=true
INGESTION_PRICE_CHANGE_THRESHOLD_PCT=2.0
INGESTION_PRICE_CHANGE_THRESHOLD_ABS=1.0
INGESTION_RAW_PAYLOAD_TTL_DAYS=30
INGESTION_RAW_PAYLOAD_MAX_BYTES=524288
```

## Best Practices

### Security

1. **Never commit `.env` file**
   - Add to `.gitignore`
   - Use env file for each deployment

2. **Use strong secrets**
   ```bash
   # Generate random keys
   openssl rand -base64 32
   ```

3. **Rotate secrets periodically**
   - Update `SECRET_KEY` quarterly
   - Update database passwords annually
   - Update API keys when compromised

4. **Restrict file permissions**
   ```bash
   chmod 600 .env
   ```

### Performance

1. **Adjust log level based on environment**
   - Development: DEBUG
   - Staging: INFO
   - Production: WARNING

2. **Configure timeouts appropriately**
   - Short timeouts (3-5s) for fast networks
   - Long timeouts (10-15s) for slower networks or heavy load

3. **Balance retry count and timeout**
   - High retries + long timeout = slow but reliable
   - Low retries + short timeout = fast but may fail more

### Monitoring

1. **Enable observability features**
   - `PROMETHEUS_ENABLED=true`
   - Configure `OTEL_EXPORTER_OTLP_ENDPOINT`

2. **Use appropriate log levels**
   - Monitor logs regularly
   - Alert on ERROR and CRITICAL levels

## Validation

Verify environment variables are correctly set:

```bash
# Check specific variable
echo $SECRET_KEY

# Verify database connection
docker-compose exec api psql $DATABASE_URL -c "SELECT 1"

# Test API connectivity
docker-compose exec api curl http://localhost:8000/api/health

# List all environment variables
docker-compose exec api env | sort
```

## Common Errors

### "psycopg2.OperationalError: could not translate host name"

Database host is incorrect or unreachable.

**Fix**: Verify `DATABASE_URL` hostname is correct and network is accessible.

### "Unable to connect to Redis at localhost:6379"

Redis connection failed.

**Fix**: Verify `REDIS_URL` is correct and Redis is running.

### "SECRET_KEY is too short"

Validation fails for too-short secret keys.

**Fix**: Generate a longer key using: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`

### "eBay API key is invalid"

API requests to eBay fail.

**Fix**: Verify `EBAY_API_KEY` is correct and has required permissions.

## Environment Variable Loading Order

Environment variables are loaded in this order (last wins):

1. Default values in code
2. `.env` file
3. `docker-compose.yml` environment section
4. System environment variables
5. `-e` flags passed to docker

## Next Steps

- [Deploy with Docker Compose](./docker-compose-vps.md) - Use these variables in deployment
- [SSL/TLS Setup](./ssl-setup.md) - Secure your application
- [Monitoring Setup](./monitoring-setup.md) - Configure observability

---

**Need to deploy?** Go to [Docker Compose Deployment](./docker-compose-vps.md)
