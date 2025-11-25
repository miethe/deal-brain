---
title: "Phase 2 - API/Worker Refactoring Implementation Plan"
description: "Detailed task breakdown for refactoring API and Worker to use Playwright microservices"
status: "draft"
created: 2025-11-20
---

# Phase 2: API/Worker Refactoring

**Duration**: 2-3 days | **Effort**: ~34 hours | **Team Size**: 4-5 engineers

## Phase Objective

Refactor API and Worker containers to use external Playwright microservices via HTTP instead of embedded Playwright functionality. Remove all Playwright dependencies from API/Worker images, reducing their size from 1.71GB to <500MB.

## Success Criteria

- [x] API container builds without Playwright (<500MB, <3 min)
- [x] Worker container builds without Playwright (<500MB, <3 min)
- [x] HTTP client wrappers created for both services
- [x] AdapterRouter successfully calls Ingestion Service
- [x] ImageGenerationService successfully calls Image Service
- [x] All integration tests pass
- [x] All end-to-end tests pass
- [x] Zero regressions in extraction or rendering quality
- [x] Docker Compose deployment works with all services
- [x] No Playwright imports in API/Worker code

---

## Task Breakdown

### Task 2.1: Create HTTP Client Wrapper for Ingestion Service

**Owner**: Python Backend Engineer
**Model**: Sonnet
**Duration**: 3 hours
**Status**: Not Started
**Depends On**: Phase 1 Complete

**Description**:
Create an HTTP client wrapper that encapsulates communication with the Playwright Ingestion Service. This wrapper will be used by AdapterRouter as a fallback adapter.

**Acceptance Criteria**:
- [ ] HTTP client wrapper created at `apps/api/dealbrain_api/adapters/http_playwright_ingestion.py`
- [ ] Implements standard Adapter interface for fallback chain integration
- [ ] Configuration:
  - [ ] Service URL from `PLAYWRIGHT_INGESTION_URL` environment variable
  - [ ] Timeout: `PLAYWRIGHT_TIMEOUT_INGESTION_S` (default 10s)
  - [ ] Retry configuration: `PLAYWRIGHT_INGESTION_RETRIES` (default 2)
- [ ] Request mapping: URL → Ingestion Service request schema
- [ ] Response mapping: Service response → Adapter response format
- [ ] Error handling:
  - [ ] Service unavailable → appropriate error code
  - [ ] Timeout → timeout error
  - [ ] Invalid response → parsing error
  - [ ] Network error → retryable error
- [ ] Circuit breaker pattern implemented (fail-fast if service unhealthy)
- [ ] Timeout handling with configurable values
- [ ] Retry logic with exponential backoff
- [ ] Request/response logging with trace IDs
- [ ] OpenTelemetry span creation for observability
- [ ] Pydantic request/response validation
- [ ] Unit tests covering all paths
- [ ] No direct Playwright imports

**Implementation Details**:

```python
# apps/api/dealbrain_api/adapters/http_playwright_ingestion.py

class HttpPlaywrightIngestionAdapter(Adapter):
    """HTTP client adapter for Playwright Ingestion Service."""

    def __init__(
        self,
        service_url: str = None,
        timeout_s: int = 10,
        retry_count: int = 2,
    ):
        self.service_url = service_url or os.getenv(
            "PLAYWRIGHT_INGESTION_URL",
            "http://localhost:8001"
        )
        self.timeout_s = timeout_s or int(os.getenv(
            "PLAYWRIGHT_TIMEOUT_INGESTION_S",
            "10"
        ))
        self.retry_count = retry_count
        self.client = httpx.AsyncClient(timeout=self.timeout_s)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60
        )

    async def extract(
        self,
        url: str,
        marketplace_type: str,
        **kwargs
    ) -> Optional[ExtractionResult]:
        """Extract listing data from URL via Ingestion Service."""
        logger.info(
            "ingestion_adapter_extract",
            extra={"url": url, "marketplace": marketplace_type}
        )

        try:
            # Check circuit breaker
            if not self.circuit_breaker.allow_request():
                logger.warning(
                    "ingestion_adapter_circuit_open",
                    extra={"service": "ingestion"}
                )
                return None

            # Create request for Ingestion Service
            request_data = {
                "url": url,
                "marketplace_type": marketplace_type,
                "timeout_s": self.timeout_s,
                "retry_count": self.retry_count
            }

            # Create OpenTelemetry span
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span("ingestion_service_call") as span:
                span.set_attribute("url", url)
                span.set_attribute("marketplace", marketplace_type)

                # Call service with retry logic
                response = await self._call_with_retry(request_data)

                if response is None:
                    self.circuit_breaker.record_failure()
                    return None

                # Parse response
                extraction = self._parse_response(response)
                self.circuit_breaker.record_success()
                return extraction

        except Exception as e:
            logger.error(
                "ingestion_adapter_error",
                exc_info=True,
                extra={"url": url}
            )
            self.circuit_breaker.record_failure()
            return None

    async def _call_with_retry(self, request_data: dict) -> Optional[dict]:
        """Call service with exponential backoff retry."""
        last_error = None

        for attempt in range(self.retry_count + 1):
            try:
                response = await self.client.post(
                    f"{self.service_url}/v1/extract",
                    json=request_data,
                    timeout=self.timeout_s
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    last_error = response.text
                    if attempt < self.retry_count:
                        backoff = 2 ** attempt  # exponential backoff
                        await asyncio.sleep(backoff)

            except httpx.TimeoutException as e:
                last_error = str(e)
                logger.warning(
                    "ingestion_service_timeout",
                    extra={"attempt": attempt + 1}
                )
                if attempt < self.retry_count:
                    await asyncio.sleep(2 ** attempt)

            except httpx.ConnectError as e:
                last_error = str(e)
                logger.warning(
                    "ingestion_service_unavailable",
                    extra={"attempt": attempt + 1}
                )
                if attempt < self.retry_count:
                    await asyncio.sleep(2 ** attempt)

        logger.error(
            "ingestion_service_failed_all_retries",
            extra={"last_error": last_error}
        )
        return None

    def _parse_response(self, response_data: dict) -> ExtractionResult:
        """Parse Ingestion Service response to adapter format."""
        return ExtractionResult(
            title=response_data.get("title"),
            price=response_data.get("price"),
            specs=response_data.get("specs", {}),
            images=response_data.get("images", []),
            extraction_confidence=response_data.get("extraction_confidence", 1.0),
            raw_data=response_data.get("raw_html"),
            metadata={
                "extraction_time_ms": response_data.get("extraction_time_ms"),
                "marketplace": response_data.get("marketplace"),
                "service": "playwright-ingestion"
            }
        )
```

**Dependencies**:
- Phase 1 complete (Ingestion Service running)
- `apps/api/dealbrain_api/adapters/base.py` (Adapter interface)

**Related Files**:
- `apps/api/dealbrain_api/adapters/router.py` (AdapterRouter integration)
- `apps/api/dealbrain_api/adapters/browser_pool.py` (to replace)
- `packages/core/schemas.py` (ExtractionResult schema)

---

### Task 2.2: Create HTTP Client Wrapper for Image Service

**Owner**: Python Backend Engineer
**Model**: Sonnet
**Duration**: 3 hours
**Status**: Not Started
**Depends On**: Phase 1 Complete

**Description**:
Create an HTTP client wrapper that encapsulates communication with the Playwright Image Service. This wrapper will replace the embedded `_html_to_image()` method in ImageGenerationService.

**Acceptance Criteria**:
- [ ] HTTP client wrapper created at `apps/api/dealbrain_api/services/http_image_renderer.py`
- [ ] Configuration:
  - [ ] Service URL from `PLAYWRIGHT_IMAGE_URL` environment variable
  - [ ] Timeout: `PLAYWRIGHT_TIMEOUT_IMAGE_S` (default 15s)
- [ ] Request mapping: HTML + config → Image Service request schema
- [ ] Response mapping: Service response → local format
- [ ] Error handling:
  - [ ] Service unavailable → appropriate error
  - [ ] Timeout → timeout error
  - [ ] Invalid HTML → validation error
  - [ ] Network error → retryable error
- [ ] Circuit breaker pattern implemented
- [ ] Timeout handling with configurable values
- [ ] Graceful degradation if service fails
- [ ] Request/response logging with trace IDs
- [ ] OpenTelemetry span creation
- [ ] Pydantic request/response validation
- [ ] Image format handling (PNG/JPEG)
- [ ] Base64 decoding from response
- [ ] Unit tests covering all paths
- [ ] No direct Playwright imports

**Implementation Details**:

```python
# apps/api/dealbrain_api/services/http_image_renderer.py

class HttpImageRenderer:
    """HTTP client for Playwright Image Service rendering."""

    def __init__(
        self,
        service_url: str = None,
        timeout_s: int = 15,
    ):
        self.service_url = service_url or os.getenv(
            "PLAYWRIGHT_IMAGE_URL",
            "http://localhost:8002"
        )
        self.timeout_s = timeout_s or int(os.getenv(
            "PLAYWRIGHT_TIMEOUT_IMAGE_S",
            "15"
        ))
        self.client = httpx.AsyncClient(timeout=self.timeout_s)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60
        )

    async def render_html_to_image(
        self,
        html: str,
        width: int = 1200,
        height: int = 630,
        image_format: str = "png",
        scale_factor: float = 2.0,
        css_overrides: str = None,
    ) -> Optional[bytes]:
        """Render HTML to image via Image Service."""
        logger.info(
            "image_renderer_render",
            extra={
                "dimensions": f"{width}x{height}",
                "format": image_format
            }
        )

        try:
            # Check circuit breaker
            if not self.circuit_breaker.allow_request():
                logger.warning(
                    "image_renderer_circuit_open",
                    extra={"service": "image"}
                )
                return None

            # Create request
            request_data = {
                "html": html,
                "width": width,
                "height": height,
                "image_format": image_format,
                "scale_factor": scale_factor,
                "timeout_s": self.timeout_s,
                "css_overrides": css_overrides
            }

            # Create OpenTelemetry span
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span("image_service_call") as span:
                span.set_attribute("dimensions", f"{width}x{height}")
                span.set_attribute("format", image_format)

                # Call service
                response = await self._call_service(request_data)

                if response is None:
                    self.circuit_breaker.record_failure()
                    return None

                # Decode response
                image_bytes = base64.b64decode(response["image_base64"])
                self.circuit_breaker.record_success()
                return image_bytes

        except Exception as e:
            logger.error(
                "image_renderer_error",
                exc_info=True,
                extra={"dimensions": f"{width}x{height}"}
            )
            self.circuit_breaker.record_failure()
            return None

    async def _call_service(self, request_data: dict) -> Optional[dict]:
        """Call Image Service."""
        try:
            response = await self.client.post(
                f"{self.service_url}/v1/render",
                json=request_data,
                timeout=self.timeout_s
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    "image_service_error",
                    extra={"status": response.status_code}
                )
                return None

        except httpx.TimeoutException:
            logger.warning("image_service_timeout")
            return None
        except httpx.ConnectError:
            logger.warning("image_service_unavailable")
            return None

    async def get_service_health(self) -> bool:
        """Check if Image Service is healthy."""
        try:
            response = await self.client.get(
                f"{self.service_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
```

**Dependencies**:
- Phase 1 complete (Image Service running)
- `apps/api/dealbrain_api/services/image_generation.py` (to refactor)

**Related Files**:
- `apps/api/dealbrain_api/services/image_generation.py` (lines 131-655)
- `packages/core/schemas.py` (ImageResponse schema)

---

### Task 2.3: Update AdapterRouter to Use HTTP Client

**Owner**: Backend Engineer
**Model**: Sonnet
**Duration**: 3 hours
**Status**: Not Started
**Depends On**: Task 2.1

**Description**:
Update the AdapterRouter fallback chain to use the new HttpPlaywrightIngestionAdapter instead of PlaywrightAdapter.

**Acceptance Criteria**:
- [ ] AdapterRouter updated to use HttpPlaywrightIngestionAdapter
- [ ] AdapterRouter fallback chain order unchanged
- [ ] PlaywrightAdapter removed from adapter list
- [ ] HTTP adapter injected with proper configuration
- [ ] Fallback logic unchanged (same behavior)
- [ ] Error handling passes through correctly
- [ ] Trace context propagated through adapter chain
- [ ] Logging maintains request correlation
- [ ] Unit tests pass for adapter chain
- [ ] Integration tests pass for URL extraction flow

**Implementation Details**:

```python
# In apps/api/dealbrain_api/adapters/router.py

from .http_playwright_ingestion import HttpPlaywrightIngestionAdapter

class AdapterRouter:
    """Route extraction to appropriate adapters."""

    def __init__(self):
        # Initialize adapters in fallback order
        self.adapters = [
            EbayAPIAdapter(),
            JSONLDAdapter(),
            HttpPlaywrightIngestionAdapter(),  # Changed from PlaywrightAdapter()
        ]

    async def extract(
        self,
        url: str,
        marketplace_type: str = None
    ) -> Optional[ExtractionResult]:
        """Try each adapter in sequence until one succeeds."""
        for adapter in self.adapters:
            try:
                logger.debug(
                    f"adapter_trying",
                    extra={
                        "adapter": adapter.__class__.__name__,
                        "url": url
                    }
                )
                result = await adapter.extract(url, marketplace_type)
                if result:
                    logger.info(
                        "extraction_succeeded",
                        extra={
                            "adapter": adapter.__class__.__name__,
                            "marketplace": marketplace_type
                        }
                    )
                    return result
            except Exception as e:
                logger.warning(
                    "adapter_failed",
                    extra={
                        "adapter": adapter.__class__.__name__,
                        "error": str(e)
                    }
                )
                continue

        logger.warning(
            "all_adapters_failed",
            extra={"url": url, "marketplace": marketplace_type}
        )
        return None
```

**Dependencies**:
- Task 2.1 (HTTP client wrapper)
- `apps/api/dealbrain_api/adapters/router.py` (exists)

**Related Files**:
- `apps/api/dealbrain_api/adapters/playwright.py` (to remove)

---

### Task 2.4: Update ImageGenerationService to Use HTTP Client

**Owner**: Backend Engineer
**Model**: Sonnet
**Duration**: 3 hours
**Status**: Not Started
**Depends On**: Task 2.2

**Description**:
Refactor ImageGenerationService to use the new HttpImageRenderer instead of embedded Playwright rendering logic.

**Acceptance Criteria**:
- [ ] ImageGenerationService updated to inject HttpImageRenderer
- [ ] `_html_to_image()` method removed from service
- [ ] All rendering calls delegated to HTTP client
- [ ] Error handling for service failures implemented
- [ ] Graceful degradation if service unavailable
- [ ] S3 caching logic preserved and unchanged
- [ ] Database updates unchanged
- [ ] Celery task handling unchanged
- [ ] All existing interfaces remain unchanged
- [ ] Unit tests pass for service logic
- [ ] Integration tests pass for card generation flow

**Implementation Details**:

```python
# In apps/api/dealbrain_api/services/image_generation.py

from .http_image_renderer import HttpImageRenderer

class ImageGenerationService:
    """Generate and cache listing card images."""

    def __init__(
        self,
        session_maker,
        s3_client,
        image_renderer: HttpImageRenderer = None
    ):
        self.session_maker = session_maker
        self.s3_client = s3_client
        self.image_renderer = image_renderer or HttpImageRenderer()

    async def generate_and_cache(
        self,
        listing_id: str,
        card_template_type: str = "default"
    ) -> Optional[str]:
        """Generate card image and cache to S3."""
        try:
            # Fetch listing
            listing = await self._get_listing(listing_id)
            if not listing:
                return None

            # Render HTML template
            html = await self._render_template(listing, card_template_type)

            # Call Image Service
            image_bytes = await self.image_renderer.render_html_to_image(
                html=html,
                width=1200,
                height=630,
                image_format="png",
                scale_factor=2.0
            )

            if not image_bytes:
                logger.warning(
                    "card_generation_failed",
                    extra={"listing_id": listing_id}
                )
                return None

            # Cache to S3
            s3_url = await self._cache_to_s3(
                listing_id,
                image_bytes,
                card_template_type
            )

            # Update listing metadata
            await self._update_listing_metadata(listing_id, s3_url)

            logger.info(
                "card_generation_succeeded",
                extra={"listing_id": listing_id, "s3_url": s3_url}
            )
            return s3_url

        except Exception as e:
            logger.error(
                "card_generation_error",
                exc_info=True,
                extra={"listing_id": listing_id}
            )
            return None

    async def _render_template(
        self,
        listing,
        card_template_type: str
    ) -> str:
        """Render Jinja2 template to HTML."""
        # ... existing template rendering logic ...
        pass

    async def _cache_to_s3(
        self,
        listing_id: str,
        image_bytes: bytes,
        template_type: str
    ) -> str:
        """Cache image to S3 with TTL."""
        # ... existing S3 caching logic ...
        pass

    async def _update_listing_metadata(
        self,
        listing_id: str,
        s3_url: str
    ) -> None:
        """Update listing with cached image URL."""
        # ... existing metadata update logic ...
        pass
```

**Dependencies**:
- Task 2.2 (HTTP client wrapper)
- `apps/api/dealbrain_api/services/image_generation.py` (exists)

**Related Files**:
- `apps/api/dealbrain_api/tasks/card_images.py` (Celery task)

---

### Task 2.5: Remove PlaywrightAdapter and browser_pool.py Imports

**Owner**: Python Backend Engineer
**Model**: Haiku
**Duration**: 2 hours
**Status**: Not Started
**Depends On**: Tasks 2.3, 2.4

**Description**:
Remove all Playwright imports, PlaywrightAdapter, and browser_pool.py from API and Worker code. Verify no remaining Playwright references.

**Acceptance Criteria**:
- [ ] `apps/api/dealbrain_api/adapters/playwright.py` removed or marked deprecated
- [ ] `apps/api/dealbrain_api/adapters/browser_pool.py` removed or marked deprecated
- [ ] All imports of PlaywrightAdapter removed
- [ ] All imports of BrowserPool removed
- [ ] All imports of playwright package removed
- [ ] Code search for "playwright" returns zero results in API code
- [ ] Code search for "browser" returns only non-Playwright references
- [ ] `__init__.py` files updated to remove deprecated exports
- [ ] No broken imports or import errors
- [ ] Tests pass after cleanup

**Commands to Verify**:
```bash
# Verify no playwright imports in API/Worker
grep -r "from playwright" apps/api/
grep -r "import playwright" apps/api/
grep -r "PlaywrightAdapter" apps/api/
grep -r "BrowserPool" apps/api/
grep -r "browser_pool" apps/api/

# Should return zero results
```

**Dependencies**:
- Task 2.3 (AdapterRouter refactored)
- Task 2.4 (ImageGenerationService refactored)

---

### Task 2.6: Update API Dockerfile to Remove Playwright

**Owner**: DevOps Engineer
**Model**: Haiku
**Duration**: 1.5 hours
**Status**: Not Started
**Depends On**: Task 2.5

**Description**:
Update API Dockerfile to remove Playwright dependencies, system packages, and browser installation. Target <500MB image size.

**Acceptance Criteria**:
- [ ] `/infra/api/Dockerfile` updated
- [ ] All Playwright installation lines removed
- [ ] All browser-related system packages removed
- [ ] pyproject.toml Playwright dependency removed (or conditional)
- [ ] Build successfully: `docker build -t dealbrain-api infra/api`
- [ ] Image size: <500MB (verify with `docker images`)
- [ ] Build time: <3 minutes
- [ ] No Playwright-related files in final image
- [ ] All necessary dependencies preserved
- [ ] Image runs successfully in Docker Compose

**Dockerfile Changes**:

```dockerfile
# Before:
RUN apt-get update && apt-get install -y \
    ca-certificates \
    fonts-liberation \
    libappindicator3-1 \
    libatk-bridge2.0-0 \
    libnss3 \
    libxss1 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

RUN pip install playwright && python -m playwright install chromium

# After:
# (Remove all of the above - no Playwright system packages or browser install)

RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*
```

**Dependencies**:
- Task 2.5 (Playwright imports removed)

**Related Files**:
- `/infra/api/Dockerfile`
- `pyproject.toml`

---

### Task 2.7: Update Worker Dockerfile to Remove Playwright

**Owner**: DevOps Engineer
**Model**: Haiku
**Duration**: 1.5 hours
**Status**: Not Started
**Depends On**: Task 2.5

**Description**:
Update Worker Dockerfile to remove Playwright dependencies and system packages. Target <500MB image size.

**Acceptance Criteria**:
- [ ] `/infra/worker/Dockerfile` updated
- [ ] All Playwright installation lines removed
- [ ] All browser-related system packages removed
- [ ] Build successfully: `docker build -t dealbrain-worker infra/worker`
- [ ] Image size: <500MB
- [ ] Build time: <3 minutes
- [ ] No Playwright-related files in final image
- [ ] Celery dependencies preserved
- [ ] Redis client preserved
- [ ] Image runs successfully in Docker Compose

**Dependencies**:
- Task 2.5 (Playwright imports removed)

**Related Files**:
- `/infra/worker/Dockerfile`

---

### Task 2.8: Add Environment Variable Configuration

**Owner**: Backend Engineer
**Model**: Haiku
**Duration**: 1.5 hours
**Status**: Not Started
**Depends On**: Tasks 2.1, 2.2

**Description**:
Add environment variable configuration for Playwright service endpoints and timeouts. Update `.env.example` and deployment documentation.

**Acceptance Criteria**:
- [ ] Environment variables documented in `.env.example`
- [ ] Configuration loaded via pydantic-settings
- [ ] Defaults provided for development (localhost:8001, localhost:8002)
- [ ] Production defaults allow service discovery
- [ ] Timeout values configurable (PLAYWRIGHT_TIMEOUT_INGESTION_S, PLAYWRIGHT_TIMEOUT_IMAGE_S)
- [ ] Retry counts configurable
- [ ] All settings validated on startup
- [ ] Configuration documentation created

**Environment Variables**:

```bash
# .env.example

# Playwright Services
PLAYWRIGHT_INGESTION_URL=http://playwright-ingestion:8000
PLAYWRIGHT_IMAGE_URL=http://playwright-image:8000
PLAYWRIGHT_TIMEOUT_INGESTION_S=10
PLAYWRIGHT_TIMEOUT_IMAGE_S=15
PLAYWRIGHT_INGESTION_RETRIES=2
```

**Configuration Code**:

```python
# apps/api/dealbrain_api/settings.py

class Settings(BaseSettings):
    # Playwright services
    playwright_ingestion_url: str = "http://localhost:8001"
    playwright_image_url: str = "http://localhost:8002"
    playwright_timeout_ingestion_s: int = 10
    playwright_timeout_image_s: int = 15
    playwright_ingestion_retries: int = 2

    class Config:
        env_file = ".env"
```

**Dependencies**:
- Task 2.1-2 (HTTP clients)

---

### Task 2.9: Implement Circuit Breaker Pattern

**Owner**: Backend/Platform Engineer
**Model**: Sonnet
**Duration**: 2.5 hours
**Status**: Not Started
**Depends On**: Tasks 2.1, 2.2

**Description**:
Implement circuit breaker pattern in both HTTP clients to prevent cascading failures when Playwright services are unavailable.

**Acceptance Criteria**:
- [ ] Circuit breaker utility created: `apps/api/dealbrain_api/core/circuit_breaker.py`
- [ ] Implements state machine: CLOSED → OPEN → HALF_OPEN → CLOSED
- [ ] CLOSED state: allow requests
- [ ] OPEN state: reject requests (fail-fast)
- [ ] HALF_OPEN state: allow limited requests to test recovery
- [ ] Configurable failure threshold (default: 5 failures)
- [ ] Configurable recovery timeout (default: 60s)
- [ ] Integrated in both HTTP clients
- [ ] Metrics exposed (state, transitions)
- [ ] Logging for state transitions
- [ ] Unit tests for all states and transitions

**Implementation Details**:

```python
# apps/api/dealbrain_api/core/circuit_breaker.py

from enum import Enum
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """Circuit breaker for preventing cascading failures."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        service_name: str = "unknown"
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.service_name = service_name
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None

    def allow_request(self) -> bool:
        """Check if request should be allowed."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if self._should_attempt_recovery():
                self.state = CircuitState.HALF_OPEN
                logger.info(
                    f"circuit_breaker_half_open",
                    extra={"service": self.service_name}
                )
                return True
            return False

        # HALF_OPEN: allow request
        return True

    def record_success(self):
        """Record successful request."""
        if self.state == CircuitState.HALF_OPEN:
            self._close()
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def record_failure(self):
        """Record failed request."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self._open()

    def _open(self):
        """Open the circuit."""
        if self.state != CircuitState.OPEN:
            self.state = CircuitState.OPEN
            logger.warning(
                "circuit_breaker_open",
                extra={"service": self.service_name}
            )

    def _close(self):
        """Close the circuit."""
        if self.state != CircuitState.CLOSED:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.last_failure_time = None
            logger.info(
                "circuit_breaker_closed",
                extra={"service": self.service_name}
            )

    def _should_attempt_recovery(self) -> bool:
        """Check if recovery timeout has elapsed."""
        if not self.last_failure_time:
            return True
        elapsed = datetime.now() - self.last_failure_time
        return elapsed.total_seconds() >= self.recovery_timeout
```

**Dependencies**:
- Task 2.1-2 (HTTP clients)

---

### Task 2.10: Implement Timeout Handling

**Owner**: Backend Engineer
**Model**: Haiku
**Duration**: 1.5 hours
**Status**: Not Started
**Depends On**: Tasks 2.1, 2.2

**Description**:
Ensure proper timeout handling in both HTTP clients with configurable values and appropriate error responses.

**Acceptance Criteria**:
- [ ] Timeout configuration in HTTP clients
- [ ] Ingestion Service timeout: default 10s, configurable
- [ ] Image Service timeout: default 15s, configurable
- [ ] Timeout exceptions caught and logged
- [ ] Timeout errors returned to caller
- [ ] No hanging connections
- [ ] Proper resource cleanup on timeout
- [ ] Unit tests for timeout scenarios
- [ ] Integration tests verify timeout handling

**Implementation** (Already in Tasks 2.1-2, but verify):

```python
# Ingestion client timeout setup
self.client = httpx.AsyncClient(timeout=self.timeout_s)

# Image client timeout setup
response = await self.client.post(
    endpoint,
    json=request_data,
    timeout=self.timeout_s
)
```

**Dependencies**:
- Task 2.1-2 (HTTP clients)

---

### Task 2.11: Write Integration Tests for API/Worker Communication

**Owner**: Test Automation Engineer
**Model**: Sonnet
**Duration**: 5 hours
**Status**: Not Started
**Depends On**: Tasks 2.1-4

**Description**:
Write comprehensive integration tests verifying API and Worker can successfully communicate with both Playwright services.

**Acceptance Criteria**:
- [ ] Integration tests in `/tests/integration/`
- [ ] Test fixtures for Docker Compose setup/teardown
- [ ] Tests for Ingestion Service integration:
  - [ ] AdapterRouter calls Ingestion Service successfully
  - [ ] Request/response mapping correct
  - [ ] Error handling for service failures
  - [ ] Circuit breaker activation
  - [ ] Timeout handling
- [ ] Tests for Image Service integration:
  - [ ] ImageGenerationService calls Image Service successfully
  - [ ] HTML rendering works end-to-end
  - [ ] Image bytes received and decoded correctly
  - [ ] Error handling for service failures
  - [ ] Circuit breaker activation
  - [ ] Timeout handling
- [ ] Worker/Celery task integration tests:
  - [ ] Card generation task calls Image Service
  - [ ] S3 caching still works
  - [ ] Database updates still work
- [ ] All integration tests pass

**Test Coverage**:

```
tests/integration/
├── test_adapter_router_ingestion.py
│   ├── test_adapter_router_calls_ingestion_service
│   ├── test_adapter_router_handles_timeout
│   ├── test_adapter_router_handles_service_failure
│   └── test_adapter_router_circuit_breaker
├── test_image_generation_service.py
│   ├── test_image_generation_calls_image_service
│   ├── test_image_generation_handles_failure
│   ├── test_image_generation_s3_caching_still_works
│   └── test_image_generation_circuit_breaker
└── test_card_generation_task.py
    ├── test_card_generation_task_with_image_service
    └── test_card_generation_task_failure_handling
```

**Dependencies**:
- Tasks 2.1-4 (HTTP clients implemented)
- Phase 1 complete (Services running)

---

### Task 2.12: Write End-to-End Tests

**Owner**: Test Automation Engineer
**Model**: Sonnet
**Duration**: 4 hours
**Status**: Not Started
**Depends On**: Tasks 2.1-4

**Description**:
Write end-to-end tests verifying complete workflows from user request through Playwright services to database.

**Acceptance Criteria**:
- [ ] E2E tests in `/tests/e2e/`
- [ ] Test fixtures for full Docker Compose stack
- [ ] URL import workflow:
  - [ ] User POSTs URL to API
  - [ ] API calls AdapterRouter
  - [ ] AdapterRouter calls Ingestion Service
  - [ ] Listing created in database
  - [ ] Response returned to user
- [ ] Card generation workflow:
  - [ ] User requests card generation
  - [ ] Celery task created
  - [ ] Worker fetches listing
  - [ ] Worker calls Image Service
  - [ ] Image cached to S3
  - [ ] Listing metadata updated
  - [ ] Task complete
- [ ] Error handling end-to-end:
  - [ ] Service failures handled gracefully
  - [ ] API/Worker continue functioning
  - [ ] Errors logged with trace IDs
- [ ] All E2E tests pass with zero regressions

**Test Structure**:

```
tests/e2e/
├── test_url_import_workflow.py
│   ├── test_import_url_complete_workflow
│   ├── test_import_url_with_ingestion_timeout
│   └── test_import_url_with_service_failure
└── test_card_generation_workflow.py
    ├── test_card_generation_complete_workflow
    ├── test_card_generation_with_service_failure
    └── test_card_generation_image_caching
```

**Dependencies**:
- Tasks 2.1-4 (All refactoring complete)
- Phase 1 complete (Services running)

---

## Phase 2 Acceptance Checklist

### Deliverables

- [ ] HTTP client wrapper for Ingestion Service created
- [ ] HTTP client wrapper for Image Service created
- [ ] AdapterRouter updated to use HTTP client
- [ ] ImageGenerationService updated to use HTTP client
- [ ] PlaywrightAdapter removed from codebase
- [ ] browser_pool.py removed from codebase
- [ ] API Dockerfile updated (no Playwright)
- [ ] Worker Dockerfile updated (no Playwright)
- [ ] Environment variable configuration added
- [ ] Circuit breaker pattern implemented
- [ ] Timeout handling implemented
- [ ] Integration tests passing
- [ ] End-to-end tests passing

### Image Size Verification

- [ ] API image: <500MB (measure with `docker images`)
- [ ] Worker image: <500MB
- [ ] Build time: <3 minutes each
- [ ] 70% size reduction achieved

### Code Quality

- [ ] No Playwright imports in API/Worker
- [ ] All code follows project conventions
- [ ] Comprehensive docstrings
- [ ] Error handling for all scenarios
- [ ] Structured logging with trace IDs
- [ ] No security vulnerabilities

### Testing

- [ ] Integration tests: all passing
- [ ] End-to-end tests: all passing
- [ ] Error scenarios tested
- [ ] Service unavailability handled
- [ ] Timeout scenarios tested
- [ ] Circuit breaker tested

### Documentation

- [ ] Configuration guide updated
- [ ] Deployment guide updated
- [ ] Error handling documented
- [ ] Environment variables documented

---

## Phase 2 Success Criteria (GATE)

**All of the following must be true to proceed to Phase 3**:

1. API image builds <500MB without Playwright
2. Worker image builds <500MB without Playwright
3. Build times reduced to <3 minutes
4. All integration tests pass
5. All end-to-end tests pass
6. Zero regressions in extraction quality
7. Zero regressions in rendering quality
8. Docker Compose deployment works with all services
9. No Playwright imports in API/Worker code
10. Circuit breaker and timeout handling tested

---

**Document Version**: 1.0
**Status**: Draft
**Last Updated**: 2025-11-20
