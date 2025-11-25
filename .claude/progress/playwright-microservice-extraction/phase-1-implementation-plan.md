---
title: "Phase 1 - Microservice Foundation Implementation Plan"
description: "Detailed task breakdown for building Playwright microservices foundation"
status: "draft"
created: 2025-11-20
---

# Phase 1: Microservice Foundation

**Duration**: 3-4 days | **Effort**: ~39 hours | **Team Size**: 4-6 engineers

## Phase Objective

Build two independent, production-ready Playwright microservices with baseline functionality, comprehensive observability, and thorough testing. Services must be deployable in Docker Compose and integrate successfully with the main API.

## Success Criteria

- [x] Both services build successfully in Docker without errors
- [x] Both services start in Docker Compose without crashing
- [x] `/health` endpoints return valid JSON responses
- [x] `/metrics` endpoints return Prometheus-formatted metrics
- [x] Unit tests pass with >80% code coverage
- [x] Integration tests verify API ↔ service HTTP communication
- [x] Performance baseline established (latency, throughput)
- [x] OpenTelemetry instrumentation complete and functional
- [x] API documentation (Swagger/OpenAPI) complete
- [x] Docker build procedures documented

---

## Task Breakdown

### Task 1.1: Create Dockerfile for Playwright Ingestion Service

**Owner**: DevOps/Infrastructure Engineer
**Model**: Sonnet
**Duration**: 2 hours
**Status**: Not Started

**Description**:
Create a production-ready Dockerfile for the Playwright Ingestion Service that includes Playwright, Chromium browser, and Python dependencies. Should follow multi-stage build pattern to minimize final image size while including necessary system packages.

**Acceptance Criteria**:
- [ ] Dockerfile created at `/infra/ingestion/Dockerfile`
- [ ] Multi-stage build (separate build and runtime stages)
- [ ] Base image: Python 3.11 slim
- [ ] Playwright and system dependencies installed
- [ ] Chromium browser installed via Playwright
- [ ] Final image size: ~1.5GB
- [ ] Build time: <5 minutes
- [ ] Builds successfully: `docker build -t playwright-ingestion infra/ingestion`
- [ ] No build warnings or security issues

**Implementation Details**:
```dockerfile
# Stage 1: Builder
FROM python:3.11-slim as builder
RUN apt-get update && apt-get install -y \
    build-essential libssl-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml poetry.lock* ./
RUN pip install poetry && poetry export -f requirements.txt > requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim
RUN apt-get update && apt-get install -y \
    ca-certificates fonts-liberation \
    [system packages for Playwright] \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /app/requirements.txt .
RUN pip install -r requirements.txt
RUN python -m playwright install chromium

COPY apps/playwright-ingestion ./
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0"]
```

**Dependencies**:
- None (foundational task)

**Related Files**:
- `/infra/api/Dockerfile` (reference for Python/FastAPI setup)
- `/infra/worker/Dockerfile` (reference for similar structure)

---

### Task 1.2: Create Dockerfile for Playwright Image Service

**Owner**: DevOps/Infrastructure Engineer
**Model**: Sonnet
**Duration**: 2 hours
**Status**: Not Started

**Description**:
Create a production-ready Dockerfile for the Playwright Image Service with identical structure to Task 1.1, but optimized for image rendering workload (different system package dependencies if needed).

**Acceptance Criteria**:
- [ ] Dockerfile created at `/infra/image/Dockerfile`
- [ ] Multi-stage build pattern
- [ ] Base image: Python 3.11 slim
- [ ] Playwright and system dependencies installed
- [ ] Chromium browser installed
- [ ] Final image size: ~1.5GB
- [ ] Build time: <5 minutes
- [ ] Builds successfully: `docker build -t playwright-image infra/image`
- [ ] Includes libraries for image processing (Pillow)

**Dependencies**:
- Task 1.1 (for reference)

**Related Files**:
- `/infra/api/Dockerfile`
- Task 1.1 Dockerfile

---

### Task 1.3: Implement FastAPI App for Ingestion Service

**Owner**: Python Backend Engineer
**Model**: Sonnet
**Duration**: 6 hours
**Status**: Not Started

**Description**:
Implement the core FastAPI application for the Playwright Ingestion Service with the `/v1/extract` endpoint. Extract logic from current `PlaywrightAdapter` implementation and adapt to microservice.

**Acceptance Criteria**:
- [ ] FastAPI app created at `/apps/playwright-ingestion/main.py`
- [ ] Project structure: `apps/playwright-ingestion/` with proper package layout
- [ ] `POST /v1/extract` endpoint implemented with request/response schemas
- [ ] Request schema: `{url, marketplace_type, timeout_s, retry_count, user_agent}`
- [ ] Response schema: `{title, price, specs, images, raw_html, extraction_confidence, extraction_time_ms, timestamp}`
- [ ] Error response schema: `{error_type, error_message, retriable, timestamp}`
- [ ] Browser pool management implemented (reuse existing browser sessions)
- [ ] Timeout handling implemented (configurable, default 10s)
- [ ] Retry logic implemented with exponential backoff
- [ ] Extraction logic ported from `apps/api/dealbrain_api/adapters/playwright.py`
- [ ] Request validation using Pydantic
- [ ] Error handling with specific error types (timeout, browser_crash, invalid_url, render_failure)
- [ ] Structured logging with request ID tracking
- [ ] Unit tests created for endpoint logic
- [ ] Integration tests created for full request/response flow

**Implementation Details**:

**Project Structure**:
```
apps/playwright-ingestion/
├── main.py                    # FastAPI app initialization
├── config.py                  # Configuration (env vars, constants)
├── models.py                  # Pydantic request/response schemas
├── services/
│   ├── __init__.py
│   ├── browser_pool.py        # Browser pool management (ported from API)
│   └── extraction.py          # Extraction logic (ported from PlaywrightAdapter)
├── routers/
│   ├── __init__.py
│   └── extract.py             # /v1/extract endpoint
├── logging.py                 # Structured logging setup
└── observability.py           # OpenTelemetry instrumentation
```

**Core Endpoint Implementation**:
```python
@router.post("/v1/extract")
async def extract(request: ExtractRequest) -> ExtractResponse:
    """Extract listing data from JavaScript-rendered marketplace pages."""
    request_id = generate_request_id()
    start_time = time.time()

    try:
        logger.info("extraction_started", extra={
            "request_id": request_id,
            "url": request.url,
            "marketplace": request.marketplace_type
        })

        # Get page from browser pool
        page = await browser_pool.get_page()

        # Navigate and extract
        extracted = await extraction_service.extract(
            page=page,
            url=request.url,
            marketplace_type=request.marketplace_type,
            timeout_s=request.timeout_s,
            retry_count=request.retry_count
        )

        elapsed_ms = (time.time() - start_time) * 1000

        return ExtractResponse(
            title=extracted["title"],
            price=extracted["price"],
            specs=extracted["specs"],
            images=extracted["images"],
            raw_html=extracted.get("html"),
            extraction_confidence=extracted.get("confidence", 1.0),
            marketplace=request.marketplace_type,
            extraction_time_ms=int(elapsed_ms),
            timestamp=datetime.utcnow()
        )

    except TimeoutError:
        return error_response("timeout", "Extraction timed out", retriable=True)
    except Exception as e:
        logger.error("extraction_failed", exc_info=True, extra={"request_id": request_id})
        return error_response("render_failure", str(e), retriable=True)
```

**Request/Response Schemas**:
```python
class ExtractRequest(BaseModel):
    url: str
    marketplace_type: str  # amazon, ebay, walmart, newegg
    timeout_s: int = 10
    retry_count: int = 2
    user_agent: Optional[str] = None

class ExtractResponse(BaseModel):
    title: str
    price: float
    specs: Dict[str, Any]
    images: List[str]
    raw_html: Optional[str] = None
    extraction_confidence: float
    marketplace: str
    extraction_time_ms: int
    timestamp: datetime

class ErrorResponse(BaseModel):
    error_type: str  # timeout, browser_crash, invalid_url, render_failure
    error_message: str
    retriable: bool
    timestamp: datetime
```

**Dependencies**:
- Task 1.1 (Dockerfile exists)
- Playwright adapter implementation from existing API code

**Related Files**:
- `apps/api/dealbrain_api/adapters/playwright.py` (source logic)
- `apps/api/dealbrain_api/adapters/browser_pool.py` (browser pool pattern)
- `packages/core/schemas.py` (shared schemas)

---

### Task 1.4: Implement FastAPI App for Image Service

**Owner**: Python Backend Engineer
**Model**: Sonnet
**Duration**: 6 hours
**Status**: Not Started

**Description**:
Implement the core FastAPI application for the Playwright Image Service with the `/v1/render` endpoint. Extract logic from current `ImageGenerationService._html_to_image()` implementation.

**Acceptance Criteria**:
- [ ] FastAPI app created at `/apps/playwright-image/main.py`
- [ ] Project structure: `apps/playwright-image/` with proper package layout
- [ ] `POST /v1/render` endpoint implemented with request/response schemas
- [ ] Request schema: `{html, width, height, image_format, scale_factor, timeout_s, css_overrides}`
- [ ] Response schema: `{image_base64, content_type, width, height, actual_width, actual_height, generation_time_ms, timestamp}`
- [ ] Error response schema: `{error_type, error_message, retriable, timestamp}`
- [ ] Browser pool management implemented
- [ ] HTML rendering with CSS/JS injection support
- [ ] Screenshot capture with specified dimensions
- [ ] PNG/JPEG format support with quality settings
- [ ] Image quality validation before response
- [ ] Timeout handling (configurable, default 15s)
- [ ] Rendering logic ported from `apps/api/dealbrain_api/services/image_generation.py`
- [ ] Request validation using Pydantic
- [ ] Error handling with specific error types
- [ ] Structured logging with request ID tracking
- [ ] Unit tests created for endpoint logic
- [ ] Integration tests created for full request/response flow

**Implementation Details**:

**Project Structure**:
```
apps/playwright-image/
├── main.py                    # FastAPI app initialization
├── config.py                  # Configuration (env vars, constants)
├── models.py                  # Pydantic request/response schemas
├── services/
│   ├── __init__.py
│   ├── browser_pool.py        # Browser pool management
│   └── rendering.py           # Rendering logic
├── routers/
│   ├── __init__.py
│   └── render.py              # /v1/render endpoint
├── logging.py                 # Structured logging setup
└── observability.py           # OpenTelemetry instrumentation
```

**Core Endpoint Implementation**:
```python
@router.post("/v1/render")
async def render(request: RenderRequest) -> RenderResponse:
    """Render HTML to image with specified dimensions."""
    request_id = generate_request_id()
    start_time = time.time()

    try:
        logger.info("render_started", extra={
            "request_id": request_id,
            "dimensions": f"{request.width}x{request.height}",
            "format": request.image_format
        })

        # Get page from browser pool
        page = await browser_pool.get_page()

        # Render HTML
        image_bytes, actual_dims = await rendering_service.render(
            page=page,
            html=request.html,
            width=request.width,
            height=request.height,
            image_format=request.image_format,
            scale_factor=request.scale_factor,
            css_overrides=request.css_overrides,
            timeout_s=request.timeout_s
        )

        elapsed_ms = (time.time() - start_time) * 1000

        return RenderResponse(
            image_base64=base64.b64encode(image_bytes).decode(),
            content_type=f"image/{request.image_format}",
            width=request.width,
            height=request.height,
            actual_width=actual_dims["width"],
            actual_height=actual_dims["height"],
            generation_time_ms=int(elapsed_ms),
            timestamp=datetime.utcnow()
        )

    except TimeoutError:
        return error_response("timeout", "Rendering timed out", retriable=True)
    except Exception as e:
        logger.error("render_failed", exc_info=True, extra={"request_id": request_id})
        return error_response("render_failure", str(e), retriable=False)
```

**Request/Response Schemas**:
```python
class RenderRequest(BaseModel):
    html: str
    width: int = 1200
    height: int = 630
    image_format: str = "png"  # png or jpeg
    scale_factor: float = 2.0
    timeout_s: int = 15
    css_overrides: Optional[str] = None

class RenderResponse(BaseModel):
    image_base64: str
    content_type: str
    width: int
    height: int
    actual_width: int
    actual_height: int
    generation_time_ms: int
    timestamp: datetime

class ErrorResponse(BaseModel):
    error_type: str  # timeout, browser_crash, render_failure, invalid_html
    error_message: str
    retriable: bool
    timestamp: datetime
```

**Dependencies**:
- Task 1.2 (Dockerfile exists)
- Image generation logic from existing API code

**Related Files**:
- `apps/api/dealbrain_api/services/image_generation.py` (source logic, lines 131-655)
- `apps/api/dealbrain_api/adapters/browser_pool.py` (browser pool pattern)

---

### Task 1.5: Implement Health Check Endpoints

**Owner**: Python Backend Engineer
**Model**: Haiku
**Duration**: 2 hours
**Status**: Not Started

**Description**:
Implement `GET /health` endpoints for both services that expose browser pool and page availability status. Used for orchestration and monitoring.

**Acceptance Criteria**:
- [ ] `/health` endpoint implemented in both services
- [ ] Response includes: `{status, browser_ready, page_pool_available, uptime_s, version}`
- [ ] Status values: "healthy", "degraded", "unhealthy"
- [ ] Endpoint returns 200 for healthy/degraded, 503 for unhealthy
- [ ] Browser pool connectivity checked
- [ ] Page pool availability tracked
- [ ] Uptime tracked since service start
- [ ] Version from package (hardcoded or from file)
- [ ] Endpoint used by Docker health checks
- [ ] Unit tests verify response format and values

**Implementation Details**:

```python
@router.get("/health")
async def health_check() -> HealthResponse:
    """Check service health and browser pool status."""
    browser_ready = await browser_pool.is_ready()
    page_available = browser_pool.available_pages > 0

    status = "healthy"
    if not browser_ready:
        status = "degraded"
    if not page_available and browser_pool.pending_requests > 10:
        status = "unhealthy"

    return HealthResponse(
        status=status,
        browser_ready=browser_ready,
        page_pool_available=browser_pool.available_pages,
        uptime_s=int(time.time() - service_start_time),
        version=VERSION
    )

class HealthResponse(BaseModel):
    status: str  # healthy, degraded, unhealthy
    browser_ready: bool
    page_pool_available: int
    uptime_s: int
    version: str
```

**Dependencies**:
- Task 1.3 (Ingestion Service app exists)
- Task 1.4 (Image Service app exists)

---

### Task 1.6: Implement Prometheus Metrics Endpoints

**Owner**: Python Backend Engineer
**Model**: Haiku
**Duration**: 2 hours
**Status**: Not Started

**Description**:
Implement `GET /metrics` endpoints for both services that expose Prometheus-compatible metrics. Include latency histograms, success/failure counters, and browser pool metrics.

**Acceptance Criteria**:
- [ ] `/metrics` endpoint implemented in both services
- [ ] Returns text/plain Prometheus format
- [ ] Includes latency histogram: `service_latency_ms` (p50, p95, p99)
- [ ] Includes success counter: `service_requests_success_total`
- [ ] Includes failure counter: `service_requests_failure_total`
- [ ] Includes timeout counter: `service_requests_timeout_total`
- [ ] Includes browser pool metrics: `browser_pool_size`, `browser_pages_available`
- [ ] Metrics collected from request handling
- [ ] Prometheus client library integration (prometheus-client)
- [ ] Unit tests verify metric collection and formatting
- [ ] Integration tests verify metrics updated correctly

**Implementation Details**:

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
request_latency = Histogram(
    'playwright_request_latency_ms',
    'Request latency in milliseconds',
    buckets=(100, 500, 1000, 2500, 5000, 10000, 15000)
)
request_success = Counter(
    'playwright_requests_success_total',
    'Total successful requests'
)
request_failure = Counter(
    'playwright_requests_failure_total',
    'Total failed requests',
    ['error_type']
)
browser_pool_available = Gauge(
    'playwright_browser_pool_available',
    'Available pages in browser pool'
)

@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from prometheus_client import generate_latest
    return Response(
        content=generate_latest(),
        media_type="text/plain; charset=utf-8"
    )

# In request handler:
with request_latency.time():
    # ... handle request ...
    request_success.inc()
```

**Dependencies**:
- Task 1.3 (Ingestion Service app exists)
- Task 1.4 (Image Service app exists)

---

### Task 1.7: Add OpenTelemetry Instrumentation

**Owner**: Backend/Observability Engineer
**Model**: Sonnet
**Duration**: 4 hours
**Status**: Not Started

**Description**:
Add comprehensive OpenTelemetry instrumentation to both services for tracing and monitoring. Include automatic FastAPI instrumentation, custom spans for business logic, and W3C Trace Context propagation.

**Acceptance Criteria**:
- [ ] OpenTelemetry SDK configured in both services
- [ ] FastAPI instrumentation enabled (automatic endpoint tracing)
- [ ] Custom spans created for key operations (browser creation, page navigation, extraction, rendering)
- [ ] Span attributes include request ID, URL, marketplace, error type
- [ ] W3C Trace Context propagation enabled
- [ ] OTEL_EXPORTER_OTLP_ENDPOINT environment variable configurable
- [ ] Traces exported to Jaeger/Grafana Tempo via OpenTelemetry collector
- [ ] Structured logging includes trace_id and span_id
- [ ] Error spans include exception information
- [ ] Unit tests verify span creation and attributes
- [ ] Integration tests verify trace propagation from API to services

**Implementation Details**:

```python
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

# Initialize tracer
otlp_exporter = OTLPSpanExporter(
    endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")
)
trace_provider = TracerProvider()
trace_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
trace.set_tracer_provider(trace_provider)

# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

# In request handler:
tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("extract_listing") as span:
    span.set_attribute("marketplace", request.marketplace_type)
    span.set_attribute("url", request.url)
    span.set_attribute("timeout_s", request.timeout_s)
    try:
        # ... extraction logic ...
        span.set_attribute("success", True)
    except Exception as e:
        span.set_attribute("error", True)
        span.record_exception(e)
        raise
```

**Dependencies**:
- Task 1.3 (Ingestion Service app exists)
- Task 1.4 (Image Service app exists)
- OpenTelemetry libraries in pyproject.toml (already present)

**Related Files**:
- `/apps/api/dealbrain_api/main.py` (reference for OTEL setup)

---

### Task 1.8: Create Docker Compose Entries

**Owner**: DevOps Engineer
**Model**: Haiku
**Duration**: 2 hours
**Status**: Not Started

**Description**:
Add both Playwright services to the `docker-compose.yml` file with proper networking, environment variables, health checks, and volume mounts.

**Acceptance Criteria**:
- [ ] Both services added to `/docker-compose.yml`
- [ ] Services on same network as API and Worker
- [ ] Environment variables set (OTEL endpoint, pool sizes, ports)
- [ ] Health check endpoints configured
- [ ] Port mappings: Ingestion 8001, Image 8002 (internal 8000)
- [ ] Depends-on relationships defined
- [ ] Logging driver configured
- [ ] Memory/CPU limits set
- [ ] Volumes for any persistent state (if needed)
- [ ] Docker Compose validates without errors: `docker-compose config`
- [ ] Both services start successfully: `docker-compose up`

**Implementation Details**:

```yaml
# In docker-compose.yml

playwright-ingestion:
  build:
    context: .
    dockerfile: ./infra/ingestion/Dockerfile
  container_name: playwright-ingestion
  ports:
    - "8001:8000"
  environment:
    OTEL_EXPORTER_OTLP_ENDPOINT: http://otel-collector:4317
    PLAYWRIGHT_BROWSER_POOL_SIZE: 3
    PLAYWRIGHT_PAGE_POOL_SIZE: 5
    LOG_LEVEL: INFO
  depends_on:
    otel-collector:
      condition: service_started
  networks:
    - dealbrain
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s
  labels:
    - "prometheus-job=playwright-ingestion"
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"

playwright-image:
  build:
    context: .
    dockerfile: ./infra/image/Dockerfile
  container_name: playwright-image
  ports:
    - "8002:8000"
  environment:
    OTEL_EXPORTER_OTLP_ENDPOINT: http://otel-collector:4317
    PLAYWRIGHT_BROWSER_POOL_SIZE: 3
    PLAYWRIGHT_PAGE_POOL_SIZE: 5
    LOG_LEVEL: INFO
  depends_on:
    otel-collector:
      condition: service_started
  networks:
    - dealbrain
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s
  labels:
    - "prometheus-job=playwright-image"
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
```

**Dependencies**:
- Task 1.1 (Ingestion Dockerfile)
- Task 1.2 (Image Dockerfile)

**Related Files**:
- `/docker-compose.yml` (main compose file)
- `/docker-compose.profiles.yml` (for reference)

---

### Task 1.9: Write Comprehensive Unit Tests

**Owner**: Test Automation Engineer
**Model**: Sonnet
**Duration**: 6 hours
**Status**: Not Started

**Description**:
Write unit tests for both services covering endpoint logic, error handling, browser pool, and response validation. Target >80% code coverage.

**Acceptance Criteria**:
- [ ] Unit tests created in `/tests/playwright-ingestion/` and `/tests/playwright-image/`
- [ ] Test coverage >80% for both services
- [ ] Endpoint tests:
  - [ ] Valid request → successful response
  - [ ] Invalid URL → error response
  - [ ] Timeout → timeout error
  - [ ] Browser crash → crash error
  - [ ] Malformed HTML → error response
- [ ] Response validation tests:
  - [ ] Response schema valid Pydantic
  - [ ] All required fields present
  - [ ] Field types correct
  - [ ] Error responses well-formatted
- [ ] Browser pool tests:
  - [ ] Pool creates pages correctly
  - [ ] Pool reuses pages
  - [ ] Pool handles exhaustion gracefully
  - [ ] Pool cleanup removes resources
- [ ] Logging tests:
  - [ ] Request logged with ID
  - [ ] Success logged
  - [ ] Errors logged with exception
- [ ] Metrics tests:
  - [ ] Metrics endpoint returns Prometheus format
  - [ ] Counters incremented correctly
  - [ ] Histogram records latency
- [ ] All tests pass: `pytest tests/ -v`
- [ ] Coverage report generated and validated

**Test Structure**:

```
tests/
├── playwright-ingestion/
│   ├── conftest.py              # Fixtures and test setup
│   ├── test_extract_endpoint.py # /v1/extract tests
│   ├── test_health.py           # /health endpoint tests
│   ├── test_metrics.py          # /metrics endpoint tests
│   ├── test_browser_pool.py     # Browser pool logic
│   ├── test_extraction_logic.py # Core extraction
│   └── test_error_handling.py   # Error scenarios
├── playwright-image/
│   ├── conftest.py
│   ├── test_render_endpoint.py  # /v1/render tests
│   ├── test_health.py
│   ├── test_metrics.py
│   ├── test_browser_pool.py
│   ├── test_rendering_logic.py
│   └── test_error_handling.py
```

**Example Tests**:

```python
# test_extract_endpoint.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_extract_valid_url():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/v1/extract",
            json={
                "url": "https://amazon.com/dp/B0C...",
                "marketplace_type": "amazon",
                "timeout_s": 10
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "title" in data
        assert "price" in data
        assert data["extraction_confidence"] > 0

@pytest.mark.asyncio
async def test_extract_invalid_url():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/v1/extract",
            json={
                "url": "invalid-url",
                "marketplace_type": "amazon"
            }
        )
        assert response.status_code in [400, 500]
        data = response.json()
        assert "error_type" in data

@pytest.mark.asyncio
async def test_metrics_format():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
        assert "playwright_request_latency_ms" in response.text
```

**Dependencies**:
- Task 1.3 (Ingestion Service)
- Task 1.4 (Image Service)
- Task 1.5-6 (Health/Metrics endpoints)

---

### Task 1.10: Write Integration Tests

**Owner**: Test Automation Engineer
**Model**: Sonnet
**Duration**: 4 hours
**Status**: Not Started

**Description**:
Write integration tests verifying both services work together with Docker Compose, including API communication via HTTP, service discovery, and end-to-end request flows.

**Acceptance Criteria**:
- [ ] Integration tests created in `/tests/integration/`
- [ ] Docker Compose starts successfully for testing
- [ ] Test fixtures for Docker service setup/teardown
- [ ] API → Ingestion Service HTTP communication test
- [ ] API → Image Service HTTP communication test
- [ ] Service health check tests
- [ ] Metrics collection tests
- [ ] Timeout handling tests
- [ ] Error propagation tests
- [ ] All integration tests pass: `pytest tests/integration/ -v`
- [ ] Test execution documented (startup time, requirements)

**Test Structure**:

```
tests/integration/
├── conftest.py                  # Docker compose fixtures
├── test_ingestion_api.py        # API → Ingestion tests
├── test_image_api.py            # API → Image tests
├── test_service_discovery.py    # Service finding/connectivity
├── test_error_propagation.py    # Error handling e2e
└── test_observability.py        # Logging/metrics integration
```

**Example Tests**:

```python
# test_ingestion_api.py
@pytest.mark.integration
async def test_api_calls_ingestion_service(docker_compose_service):
    """Test that API successfully calls Ingestion Service."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/v1/import?url=...",
            json={"url": "https://amazon.com/dp/B0C..."}
        )
        assert response.status_code == 200
        data = response.json()
        assert "listing" in data

@pytest.mark.integration
async def test_ingestion_service_timeout(docker_compose_service):
    """Test timeout handling in Ingestion Service."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/v1/extract",
            json={
                "url": "https://slow-site.invalid",
                "timeout_s": 1  # Very short timeout
            },
            timeout=10
        )
        # Should timeout or fail gracefully
        assert response.status_code in [408, 500]
        data = response.json()
        assert data["error_type"] == "timeout"
```

**Dependencies**:
- Task 1.1-2 (Dockerfiles)
- Task 1.3-4 (Services)
- Task 1.8 (Docker Compose)

---

### Task 1.11: Create Documentation

**Owner**: Documentation Writer
**Model**: Haiku
**Duration**: 3 hours
**Status**: Not Started

**Description**:
Create comprehensive documentation for Phase 1 deliverables including API specifications, Docker build procedures, configuration guide, and deployment instructions.

**Acceptance Criteria**:
- [ ] API documentation created: `docs/api/playwright-services.md`
- [ ] OpenAPI/Swagger specs generated automatically
- [ ] Docker build guide created: `docs/deployment/playwright-docker-build.md`
- [ ] Configuration guide created: `docs/configuration/playwright-services-config.md`
- [ ] Docker Compose deployment guide: `docs/deployment/playwright-docker-compose.md`
- [ ] Troubleshooting guide created: `docs/troubleshooting/playwright-services-troubleshooting.md`
- [ ] Performance baseline documented: `docs/performance/playwright-services-baseline.md`
- [ ] All documentation includes examples and code snippets
- [ ] YAML frontmatter added to all markdown files
- [ ] Links validated
- [ ] Images included where helpful (architecture diagrams)

**Documentation Structure**:

```
docs/
├── api/
│   └── playwright-services.md           # API reference
├── deployment/
│   ├── playwright-docker-build.md       # Build instructions
│   ├── playwright-docker-compose.md     # Local deployment
│   └── playwright-services-deployment.md # General deployment
├── configuration/
│   └── playwright-services-config.md    # Configuration reference
├── troubleshooting/
│   └── playwright-services-troubleshooting.md # Common issues
└── performance/
    └── playwright-services-baseline.md  # Baseline metrics
```

**Documentation Content**:

**API Documentation**:
- Endpoint reference with request/response schemas
- Error codes and meanings
- Example requests and responses
- Rate limits and quotas (if applicable)
- Authentication (if applicable)
- Auto-generated Swagger UI available at `/docs`

**Docker Build Guide**:
- Prerequisites (Docker version)
- Build commands with examples
- Image size expectations
- Build time expectations
- Dockerfile locations and structure

**Configuration Guide**:
- Environment variables
- Default values
- How to set each variable
- Impact of each configuration

**Deployment Guide**:
- Docker Compose setup
- Service dependencies
- Network configuration
- Health check verification
- Troubleshooting startup issues

**Dependencies**:
- Task 1.1-10 (All services complete)

**Related Files**:
- `/docs/` (documentation directory)
- `docker-compose.yml` (reference for config)

---

## Phase 1 Acceptance Checklist

### Deliverables

- [ ] Dockerfile for Ingestion Service created and building
- [ ] Dockerfile for Image Service created and building
- [ ] Ingestion Service FastAPI app complete with `/v1/extract` endpoint
- [ ] Image Service FastAPI app complete with `/v1/render` endpoint
- [ ] Health check endpoints implemented in both services
- [ ] Prometheus metrics endpoints implemented in both services
- [ ] OpenTelemetry instrumentation complete
- [ ] Docker Compose configuration updated with both services
- [ ] Unit tests passing with >80% coverage
- [ ] Integration tests passing and verifying service communication
- [ ] Documentation complete with API specs and guides

### Quality Standards

- [ ] Code follows existing project conventions
- [ ] All functions have docstrings
- [ ] Error handling covers all scenarios
- [ ] Logging includes request IDs and context
- [ ] No security vulnerabilities detected
- [ ] Performance baseline established and documented

### Testing

- [ ] Unit tests: >80% coverage
- [ ] Integration tests: all passing
- [ ] Docker images: build successfully
- [ ] Services: start and respond to health checks
- [ ] Metrics: collected and exposed correctly
- [ ] Traces: exported to Jaeger/Grafana

### Documentation

- [ ] API documentation complete
- [ ] Docker build guide complete
- [ ] Configuration guide complete
- [ ] Deployment guide complete
- [ ] Troubleshooting guide complete
- [ ] Performance baseline documented

---

## Phase 1 Success Criteria (GATE)

**All of the following must be true to proceed to Phase 2**:

1. Both services build successfully in Docker
2. Both services start in Docker Compose without errors
3. Health endpoints return 200 with valid JSON
4. Metrics endpoints return Prometheus-formatted output
5. Unit tests pass with >80% code coverage
6. Integration tests pass with API communication verified
7. Performance baseline established (latency <10s ingestion, <15s image)
8. OpenTelemetry instrumentation working (traces visible)
9. Zero security vulnerabilities detected
10. Documentation complete and reviewed

---

## Phase 1 Context Notes

See `phase-1-context.md` for technical decisions and implementation notes.

---

**Document Version**: 1.0
**Status**: Draft
**Last Updated**: 2025-11-20
