---
title: "Playwright Microservice Extraction"
description: "Extract Playwright functionality into two separate microservices for independent scaling, reduced image sizes, and improved separation of concerns"
audience: [ai-agents, developers, devops, pm]
tags: [playwright, microservices, docker, infrastructure, scalability]
created: 2025-11-20
updated: 2025-11-20
category: "product-planning"
status: draft
related:
  - /docs/architecture/playwright-optimization-analysis.md
  - /docs/development/docker-optimization.md
  - /docs/project_plans/playwright-infrastructure/playwright-infrastructure-v1.md
---

# Playwright Microservice Extraction

## Feature Brief & Metadata

**Feature Name:**
> Playwright Microservice Extraction - Phase 2 Infrastructure Modernization

**Filepath Name:**
> `playwright-microservice-extraction-v1`

**Date:**
> 2025-11-20

**Category:**
> Infrastructure Enhancement

**Related Documents:**
> - Architecture Analysis: `/docs/architecture/playwright-optimization-analysis.md`
> - Docker Optimization Guide: `/docs/development/docker-optimization.md`
> - Playwright Infrastructure PRD: `/docs/project_plans/playwright-infrastructure/playwright-infrastructure-v1.md`

---

## 1. Executive Summary

This PRD addresses the next phase of Playwright optimization by extracting browser automation into two dedicated microservices. Phase 1 (multi-stage Docker builds) reduces development image bloat; Phase 2 removes Playwright entirely from the main API and Worker containers by offloading functionality to specialized, independently-scalable services.

**Key Outcomes:**
- Remove 1.1GB Playwright dependencies from API and Worker images
- Enable independent scaling of browser automation tasks in production
- Achieve 100% functional parity with zero regression
- Separate concerns: core listing operations vs. browser automation

**Priority:** HIGH

**Success Metrics:**
- API image size: 1.71GB → <500MB (70% reduction)
- Worker image size: 1.71GB → <500MB (70% reduction)
- API build time: 5-6 minutes → <3 minutes (50% reduction)
- Playwright Ingestion Service: <10s latency per URL extraction
- Playwright Image Service: <15s latency per card render
- Production deployment with zero downtime transition

---

## 2. Context & Background

### Current State

The Playwright infrastructure optimization (Phase 1) introduced multi-stage Docker builds to separate development and production images. However, Playwright dependencies remain in production images for two distinct use cases:

1. **URL Ingestion** (PlaywrightAdapter): Extract listing data from JavaScript-rendered marketplace pages as fallback in the adapter chain
2. **Card Image Generation** (ImageGenerationService): Render listing cards as PNG/JPEG images for social media sharing

Both use cases run in the API and Worker containers, requiring Playwright in production images. This creates:
- Large image sizes (1.71GB per container)
- Tight coupling between core API and browser automation
- Limited independent scalability for browser-heavy workloads
- Increased memory/CPU requirements for all instances

### Problem Space

**Primary Problems:**

1. **Monolithic API Container:**
   - API container carries 1.1GB of Playwright overhead it only occasionally uses
   - Cannot independently scale Playwright functionality without scaling entire API
   - Browser crashes or failures can impact core API stability

2. **No Independent Playwright Scaling:**
   - URL extraction and card generation compete for resources on same container
   - Cannot run 10 card generators while keeping API lightweight
   - Capacity planning requires provisioning for peak Playwright usage across all instances

3. **Tight Coupling:**
   - ImageGenerationService embedded in API creates complexity
   - PlaywrightAdapter tightly integrated into adapter chain
   - Difficult to debug browser issues separately from API issues
   - Version updates to Playwright affect entire API deployment

4. **Operational Inefficiency:**
   - Starting/stopping API instance requires Playwright browser lifecycle management
   - Memory usage spike for card generation affects API response times
   - Browser pool connections consume API resources during peak usage

### Current Alternatives / Workarounds

**What Exists Today:**
- Multi-stage Docker builds (Phase 1) separate dev/prod, but production still includes Playwright
- ImageGenerationService in API handles card generation synchronously with result caching
- PlaywrightAdapter as priority-10 fallback in adapter chain for URL extraction
- BrowserPool class manages Chromium browser instances and page reuse

**Why Insufficient:**
- Development still requires rebuilding with Playwright dependencies if testing card generation
- No independent scaling possible—must scale entire API to scale Playwright
- Browser resource contention with core API operations
- Difficult to independently monitor, troubleshoot, and optimize browser automation
- Card generation blocking under high load (Celery tasks compete with API threads)

### Architectural Context

Deal Brain follows a layered service architecture:

- **API Layer**: FastAPI routers handling HTTP requests, validation, and DTOs
- **Service Layer**: Business logic orchestration, calling repositories and domain functions
- **Repository Layer**: Database operations, query construction, RLS enforcement
- **Domain Logic**: Shared in `packages/core/` (valuation, scoring, schemas)
- **External Services**: Adapters, image generation, external marketplace APIs

The Playwright microservices will follow the same principles:
- Accept standardized Pydantic DTO requests
- Return standardized DTOs via HTTP REST
- Emit OpenTelemetry spans for observability
- Expose Prometheus metrics endpoints
- Include health check endpoints for orchestration

---

## 3. Problem Statement

**Core Gap:**
Playwright functionality (URL extraction and card rendering) is embedded in production API and Worker containers, creating a monolithic system that cannot independently scale browser automation workloads or isolate browser-related failures from core operations.

**Root Cause:**
1. PlaywrightAdapter integrated directly into adapter fallback chain (adapters/browser_pool.py)
2. ImageGenerationService embedded in API services with synchronous Celery task execution
3. BrowserPool instances created and managed per API/Worker process
4. No abstraction layer for browser automation—direct in-process usage

**Technical Impact:**
- Each API instance carries full Playwright overhead (1.1GB image size, high memory usage)
- No way to provision dedicated browser automation capacity separate from API capacity
- Browser failures can destabilize API (resource exhaustion, process crashes)
- Concurrent card generation or URL extraction can spike API resource usage

**Business Impact:**
- Higher infrastructure costs (pay for Playwright overhead on every API instance)
- Limited ability to scale card generation for marketing/sharing features
- Degraded user experience during high-load periods when browser tasks compete with API
- Difficult to troubleshoot browser-related issues due to tight coupling

---

## 4. Goals & Success Metrics

### Primary Goals

**Goal 1: Remove Playwright from Main Services**
- Extract Playwright functionality into two dedicated microservices
- Ensure API and Worker images contain zero Playwright dependencies
- Achieve 70% reduction in image sizes and build times

**Goal 2: Enable Independent Scaling**
- Playwright services can scale independently from API and Worker
- Can provision dedicated Playwright resources for peak loads
- Support horizontal scaling (multiple Playwright service instances)

**Goal 3: Maintain 100% Functional Parity**
- All existing URL extraction capabilities preserved
- All existing card generation capabilities preserved
- No regression in extraction success rates, rendering quality, or performance

**Goal 4: Improve Operational Visibility**
- Separate monitoring and alerting for Playwright services
- Independent health checks for browser automation
- Clear metrics for URL extraction latency, card generation success, browser pool utilization

### Success Metrics

| Metric | Baseline | Target | Measurement Method |
|--------|----------|--------|-------------------|
| API image size | 1.71GB | <500MB | `docker images \| grep dealbrain-api` |
| Worker image size | 1.71GB | <500MB | `docker images \| grep dealbrain-worker` |
| API build time | 5-6 min | <3 min | `time docker build ...` (no Playwright install) |
| Worker build time | 5-6 min | <3 min | `time docker build ...` (no Playwright install) |
| Playwright Ingestion Service build time | N/A | <5 min | `time docker build ...` (with Playwright) |
| Playwright Image Service build time | N/A | <5 min | `time docker build ...` (with Playwright) |
| URL extraction success rate | 85%+ | 85%+ | Test suite validation |
| Card generation success rate | 95%+ | 95%+ | Test suite validation |
| Ingestion Service latency (p95) | N/A | <10s | Prometheus histogram |
| Image Service latency (p95) | N/A | <15s | Prometheus histogram |
| Production deployment downtime | N/A | 0 | Zero-downtime blue-green deployment |
| API memory usage (idle) | ~200MB | ~150MB | Container runtime metrics |
| Service integration test coverage | N/A | >90% | Coverage report |

---

## 5. Scope

### In Scope

**Microservice 1: Playwright Ingestion Service**
- Extract listing data from JavaScript-rendered marketplace pages
- Replace embedded PlaywrightAdapter and browser_pool implementations
- Provide HTTP REST API for URL extraction requests
- Support retry logic and timeout configuration
- Integrate with AdapterRouter fallback chain via HTTP client
- Full error handling and observability

**Microservice 2: Playwright Image Service**
- Render listing cards as PNG/JPEG images
- Replace ImageGenerationService._html_to_image() implementation
- Accept HTML template and rendering configuration via HTTP
- Return image bytes and metadata
- Cache control and cleanup
- Full error handling and observability

**API/Worker Refactoring**
- Remove PlaywrightAdapter and browser_pool.py imports
- Update AdapterRouter to use HTTP client for ingestion service
- Refactor ImageGenerationService to use HTTP client for rendering
- Remove all Playwright dependencies from pyproject.toml (when used by API/Worker)
- Update Dockerfiles to remove Playwright system packages and browser installation
- Maintain backward compatibility in public APIs

**Infrastructure Updates**
- Create new Dockerfiles for both Playwright services
- Update docker-compose.yml with new services
- Update CI/CD pipelines for new build targets
- Document deployment procedures for both services

**Testing & Validation**
- Unit tests for microservice API endpoints
- Integration tests for API/Worker communication with services
- End-to-end tests for complete workflows (URL extraction → listing creation)
- Performance benchmarks for latency and throughput
- Observability validation (metrics, traces, logs)

### Out of Scope

**Explicitly Excluded:**
- Rewriting or optimizing extraction/rendering algorithms (preserve existing logic)
- Changing the adapter fallback chain behavior (only add HTTP abstraction)
- Modifying S3 caching strategy (keep as-is, can migrate separately if needed)
- Database schema changes (leverage existing models)
- Authentication/authorization systems (assume internal network only initially)
- Serverless/Kubernetes deployment (focus on Docker Compose and manual deployment)
- Performance optimization beyond baseline (optimization is future phase)

**Future Phases (Not This PRD):**
- GraphQL API support
- gRPC protocol replacement
- Browser pooling optimization (connection pooling, prewarming)
- ML-based extraction confidence scoring
- Serverless deployment (AWS Lambda, Google Cloud Run)
- Kubernetes-native deployment with auto-scaling
- Multi-tenancy support
- Rate limiting and quota management

---

## 6. Requirements

### 6.1 Functional Requirements

**Playwright Ingestion Service:**

| ID | Requirement | Priority | Notes |
| :-: | ----------- | :------: | ----- |
| FR-1 | Service accepts HTTP POST `/v1/extract` with URL and marketplace type | Must | Request schema: `{url, marketplace_type, timeout_s, retry_count}` |
| FR-2 | Service extracts title, price, specs, image URL from JavaScript-rendered pages | Must | Reuse existing PlaywrightAdapter logic |
| FR-3 | Service returns structured response with extracted fields and metadata | Must | Response: `{title, price, specs, images, raw_html, extraction_confidence, timestamp}` |
| FR-4 | Service includes request/response logging with trace IDs | Must | Structured JSON logs, OpenTelemetry context propagation |
| FR-5 | Service exposes Prometheus metrics for latency, success rate, failures | Must | Histogram for latency, counters for outcomes |
| FR-6 | Service validates extracted data against expected schema | Should | Reject partial/malformed extractions, return detailed error info |
| FR-7 | Service implements timeout (default 10s, configurable) | Must | Kill hanging browser processes, return timeout error |
| FR-8 | Service supports retry logic with exponential backoff | Should | Configurable retry count and backoff strategy |
| FR-9 | Service health check endpoint returns browser pool status | Must | `GET /health` returns `{status, browser_ready, page_pool_available}` |
| FR-10 | Service gracefully handles browser crashes and reconnects | Should | Auto-recover from Chromium process failures |

**Playwright Image Service:**

| ID | Requirement | Priority | Notes |
| :-: | ----------- | :------: | ----- |
| FR-11 | Service accepts HTTP POST `/v1/render` with HTML template and config | Must | Request: `{html, width, height, image_format, scale_factor}` |
| FR-12 | Service renders HTML to PNG/JPEG image with configurable dimensions | Must | Reuse existing ImageGenerationService rendering logic |
| FR-13 | Service returns image bytes with content-type and metadata | Must | Response: `{image_bytes, content_type, width, height, generation_time_ms}` |
| FR-14 | Service includes request/response logging with trace IDs | Must | Structured JSON logs, OpenTelemetry context propagation |
| FR-15 | Service exposes Prometheus metrics for latency, success rate, failures | Must | Histogram for latency, counters for outcomes |
| FR-16 | Service validates image quality before returning | Should | Check dimensions, file size, content validity |
| FR-17 | Service implements timeout (default 15s, configurable) | Must | Kill hanging render processes, return timeout error |
| FR-18 | Service health check endpoint returns browser pool status | Must | `GET /health` returns `{status, browser_ready, page_pool_available}` |
| FR-19 | Service supports cleanup of incomplete renders | Should | Memory management, process cleanup on error |
| FR-20 | Service supports CSS/JavaScript injection for rendering | Could | Allow custom styling for specific card types |

**API/Worker Integration:**

| ID | Requirement | Priority | Notes |
| :-: | ----------- | :------: | ----- |
| FR-21 | AdapterRouter discovers and calls Ingestion Service via HTTP | Must | Fallback chain integration point |
| FR-22 | ImageGenerationService calls Image Service via HTTP for rendering | Must | Async task execution flow preserved |
| FR-23 | API/Worker gracefully degrade if Playwright services unavailable | Should | Fallback behavior: skip extraction, skip image generation |
| FR-24 | Configuration controls Playwright service endpoints (env vars) | Must | `PLAYWRIGHT_INGESTION_URL`, `PLAYWRIGHT_IMAGE_URL` |
| FR-25 | HTTP client implements retry logic and circuit breaker pattern | Should | Prevent cascading failures, handle service downtime |
| FR-26 | All API/Worker functionality works without Playwright installed locally | Must | No Playwright imports or runtime dependencies in API/Worker code |

### 6.2 Non-Functional Requirements

**Performance:**
- Ingestion Service URL extraction latency p95: <10 seconds (includes browser startup and page render)
- Image Service card rendering latency p95: <15 seconds (includes browser startup, render, screenshot)
- Ingestion Service throughput: >100 concurrent requests (with multiple instances)
- Image Service throughput: >50 concurrent renders (with multiple instances)
- Browser pool connection reuse: >80% of requests (reduce startup overhead)
- Memory usage per service instance: <1GB (with active browser)

**Reliability:**
- Service availability: 99.5% (acceptable for non-critical features)
- Graceful degradation: API/Worker continue functioning if Playwright services unavailable
- Browser crash recovery: Automatic reconnection within 5 seconds
- Page pool recovery: Handles exhausted pools without hanging
- Data consistency: No data loss if service fails mid-request

**Security:**
- Services only accept requests from internal network (Docker Compose network)
- Services validate and sanitize all input (URLs, HTML content)
- Services do not process external marketplace credentials
- Services log errors without exposing sensitive information
- Services reject oversized payloads (configurable max sizes)

**Observability:**
- OpenTelemetry spans for all operations (extraction, rendering, browser lifecycle)
- Structured JSON logging with trace_id, span_id, request_id correlation
- Prometheus metrics: histograms for latency, counters for success/failure/timeout
- Health check endpoints expose browser pool and page availability
- Error categories: timeout, browser_crash, rendering_failure, invalid_input, network_error
- Trace propagation: W3C Trace Context from API → Playwright services

**Maintainability:**
- Shared Pydantic schemas via `packages/core/` (reuse existing models)
- Clear error messages and debugging logs
- Configuration management via environment variables
- Comprehensive docstrings for all APIs
- Unit test coverage >80% for new code
- Integration test coverage for all integration points

**Deployability:**
- Services deployable via docker-compose (development)
- Services deployable to Kubernetes/swarm (future-ready)
- Zero-downtime deployment support (health checks + load balancer)
- Service discovery via DNS/environment variables
- Graceful shutdown: drain in-flight requests before terminating
- Database migrations (if needed): handled before service startup

---

## 7. Architecture

### System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         CURRENT ARCHITECTURE                          │
├──────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  API Container (1.71GB)                                      │   │
│  │  ┌────────────────────────────────────────────────────────┐  │   │
│  │  │ FastAPI App                                            │  │   │
│  │  │  ├─ AdapterRouter (with PlaywrightAdapter embedded)   │  │   │
│  │  │  ├─ ImageGenerationService (with embedded BrowserPool)│  │   │
│  │  │  └─ Core API endpoints                                │  │   │
│  │  └────────────────────────────────────────────────────────┘  │   │
│  │  ┌────────────────────────────────────────────────────────┐  │   │
│  │  │ Dependencies:                                          │  │   │
│  │  │  • playwright (132MB)                                  │  │   │
│  │  │  • chromium browser (~400MB)                           │  │   │
│  │  │  • system packages (33 packages, ~200MB)               │  │   │
│  │  └────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Worker Container (1.71GB) - Same as API                     │   │
│  │  • Celery task execution                                     │   │
│  │  • Carries full Playwright overhead                          │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘

Problems:
  ✗ 1.1GB Playwright overhead per container
  ✗ Cannot scale Playwright independently
  ✗ Browser failures affect core API
  ✗ No separation of concerns
```

### Proposed Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                      PROPOSED ARCHITECTURE                            │
├──────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌────────────────────────┐                                          │
│  │ API Container (<500MB) │                                          │
│  │ ┌──────────────────┐   │      HTTP        ┌──────────────────┐   │
│  │ │ FastAPI App      │   │     /v1/extract  │  Ingestion Svc   │   │
│  │ │ • AdapterRouter  ├──────────────────────│  (with Playwright)   │
│  │ │ • Image Gen Svc  │   │                  │                  │   │
│  │ │ • Core Endpoints │   │      HTTP        │  Browser Pool    │   │
│  │ └──────────────────┘   │     /v1/render   │  Chromium        │   │
│  │                        │                  │  URL: env var    │   │
│  │ Dependencies:          │                  └──────────────────┘   │
│  │ • sqlalchemy           │                                          │
│  │ • fastapi              │      HTTP        ┌──────────────────┐   │
│  │ • (NO playwright)      ├──────────────────│  Image Svc       │   │
│  │                        │                  │  (with Playwright)   │
│  └────────────────────────┘                  │                  │   │
│                                              │  Browser Pool    │   │
│  ┌────────────────────────┐                  │  Chromium        │   │
│  │ Worker Container       │                  │  URL: env var    │   │
│  │ (<500MB)               │                  └──────────────────┘   │
│  │ ┌──────────────────┐   │                                          │
│  │ │ Celery Tasks     │   │      HTTP                               │
│  │ │ • Card Gen Tasks ├─────────/v1/render (to Image Svc)          │
│  │ │ • Other Tasks    │   │                                          │
│  │ └──────────────────┘   │                                          │
│  │                        │                                          │
│  │ Dependencies:          │                                          │
│  │ • celery               │                                          │
│  │ • redis                │                                          │
│  │ • (NO playwright)      │                                          │
│  └────────────────────────┘                                          │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘

Benefits:
  ✓ 70% reduction in API/Worker image sizes
  ✓ Independent scaling of Playwright services
  ✓ Browser failures isolated from core API
  ✓ Clear separation of concerns
  ✓ Faster deployments for core services
```

### Service APIs

**Playwright Ingestion Service - REST API:**

```yaml
POST /v1/extract
  Request:
    {
      "url": "https://www.amazon.com/dp/B0C...",
      "marketplace_type": "amazon" | "ebay" | "walmart" | "newegg",
      "timeout_s": 10,
      "retry_count": 2,
      "user_agent": "optional override"
    }
  Response (200):
    {
      "title": "Item Title",
      "price": 499.99,
      "specs": {
        "cpu": "Intel Core i7-12700K",
        "ram_gb": 16,
        "storage": "512GB SSD"
      },
      "images": ["url1", "url2"],
      "raw_html": "base64 encoded or null",
      "extraction_confidence": 0.95,
      "marketplace": "amazon",
      "extraction_time_ms": 3500,
      "timestamp": "2025-11-20T15:30:00Z"
    }
  Response (400/408/500):
    {
      "error_type": "timeout" | "browser_crash" | "invalid_url" | "render_failure",
      "error_message": "detailed message",
      "retriable": true,
      "timestamp": "2025-11-20T15:30:00Z"
    }

GET /health
  Response:
    {
      "status": "healthy" | "degraded" | "unhealthy",
      "browser_ready": true,
      "page_pool_available": 5,
      "uptime_s": 86400,
      "version": "1.0.0"
    }

GET /metrics
  Response: Prometheus metrics (text/plain)
```

**Playwright Image Service - REST API:**

```yaml
POST /v1/render
  Request:
    {
      "html": "<html>...</html>",
      "width": 1200,
      "height": 630,
      "image_format": "png" | "jpeg",
      "scale_factor": 2,
      "timeout_s": 15,
      "css_overrides": "optional css string"
    }
  Response (200):
    {
      "image_base64": "iVBORw0KGgoAAAANS...",
      "content_type": "image/png",
      "width": 1200,
      "height": 630,
      "actual_width": 1200,
      "actual_height": 630,
      "generation_time_ms": 2800,
      "timestamp": "2025-11-20T15:30:00Z"
    }
  Response (400/408/500):
    {
      "error_type": "timeout" | "browser_crash" | "render_failure" | "invalid_html",
      "error_message": "detailed message",
      "retriable": true,
      "timestamp": "2025-11-20T15:30:00Z"
    }

GET /health
  Response:
    {
      "status": "healthy" | "degraded" | "unhealthy",
      "browser_ready": true,
      "page_pool_available": 3,
      "uptime_s": 86400,
      "version": "1.0.0"
    }

GET /metrics
  Response: Prometheus metrics (text/plain)
```

### Data Flow

**URL Extraction Flow:**

```
┌─────────────────────────────────────────────────────────────────┐
│  User imports marketplace listing via API                        │
│  POST /v1/listings/import?url=https://amazon.com/dp/B0C...      │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  API: ListingsService.import_from_url()                         │
│  Calls AdapterRouter.extract(url)                               │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  AdapterRouter Fallback Chain:                                  │
│  1. Try eBayAPIAdapter (if configured)                          │
│  2. Try JSONLDAdapter (static HTML parsing)                     │
│  3. Try PlaywrightAdapter [NEW - HTTP CLIENT]                   │
│     ├─ HTTP POST to Ingestion Service                           │
│     ├─ Wait for response (timeout: 10s)                         │
│     └─ Return extracted data                                    │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  Ingestion Service (separate container)                         │
│  1. Validate URL and marketplace type                           │
│  2. Launch Chromium browser (or reuse from pool)                │
│  3. Navigate to URL with anti-detection headers                 │
│  4. Wait for JavaScript to render (configurable timeout)        │
│  5. Extract structured data using CSS selectors                 │
│  6. Close page and return to pool                               │
│  7. Return JSON response                                        │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  API: Continue with extracted data                              │
│  • Create/update listing in database                            │
│  • Trigger metrics calculation                                  │
│  • Return success response                                      │
└─────────────────────────────────────────────────────────────────┘
```

**Card Image Generation Flow:**

```
┌─────────────────────────────────────────────────────────────────┐
│  Celery task: generate_card_images (triggered by user action)   │
│  Input: listing_id, card_template_type                          │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  Worker: ImageGenerationService.generate_and_cache()            │
│  1. Fetch listing data from database                            │
│  2. Render HTML template (Jinja2)                               │
│  3. Call Image Service via HTTP POST                            │
│  4. Receive image bytes from service                            │
│  5. Cache image to S3 with TTL                                  │
│  6. Update listing metadata with image URL                      │
│  7. Return success/error status                                 │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  Image Service (separate container)                             │
│  1. Validate HTML and render configuration                      │
│  2. Launch Chromium browser (or reuse from pool)                │
│  3. Render HTML with CSS/JS injection                           │
│  4. Take screenshot of specified dimensions                     │
│  5. Convert to PNG/JPEG with quality settings                   │
│  6. Validate image quality and dimensions                       │
│  7. Close page and return to pool                               │
│  8. Return image base64 and metadata                            │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  Worker: Continue with image handling                           │
│  • Upload to S3                                                 │
│  • Update database metadata                                     │
│  • Log completion                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. Dependencies & Assumptions

### External Dependencies

- **Playwright Python library**: 1.40.0+ (installed in Playwright services only)
- **Chromium browser**: Latest (installed in Playwright services only)
- **httpx**: HTTP client for API/Worker → Playwright services (if not already present)
- **pydantic**: Data validation (already in use)
- **OpenTelemetry**: Trace/metric instrumentation (already in use)

### Internal Dependencies

- **packages/core/schemas**: Pydantic models for DTO validation
- **apps/api/dealbrain_api/adapters**: Current adapter implementations (to refactor)
- **apps/api/dealbrain_api/services/image_generation.py**: Current card generation (to refactor)
- **Docker infrastructure**: Dockerfiles for new services
- **Docker Compose**: Orchestration for development

### Assumptions

- Playwright services run on internal network (Docker Compose network or private subnet)
- No authentication needed between API and Playwright services (internal only)
- Playwright services are stateless (can be replicated horizontally)
- Browser pool size determined by available system resources (configurable)
- S3 caching for images continues as-is (can be refactored later)
- Backward compatibility required for all public APIs
- Zero-downtime deployment achievable via blue-green strategy
- All browser automation use cases captured in two services (no hidden dependencies)

### Feature Flags

No feature flags proposed for this extraction. The services either work or fail; degradation is handled by try/catch in API/Worker.

---

## 9. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
| ----- | :----: | :--------: | ---------- |
| Playwright service unavailable → URL extraction fails | Medium | Medium | Implement circuit breaker; log warnings; skip extraction if service down |
| Network latency between API and Playwright increases response time | Medium | Medium | Add timeout (10s) and configure HTTP pool size; cache extractions in Redis |
| Browser crash under high load → requests fail | High | Medium | Implement auto-recovery; monitor browser process; implement request queuing |
| Memory leak in browser pool → OOM killer terminates service | High | Low | Monitor memory; implement page pool limits; periodic browser restart |
| Playwright service bugs expose production issues | Medium | Low | Comprehensive testing; monitoring; ability to quickly rollback to API-embedded version |
| Database/S3 dependencies missed during refactoring | High | Low | Integration tests cover all data flows; manual QA testing on staging |
| Container orchestration/networking issues | Medium | Low | Test in Docker Compose first; document deployment procedures |
| Extraction success rate drops due to behavioral changes | High | Low | Comprehensive testing against baseline; side-by-side A/B testing before cutover |
| No recovery mechanism if image service crashes mid-render | Medium | Low | Implement timeout and auto-cleanup; document manual recovery procedures |
| Playwright updates break functionality | Medium | Low | Pin Playwright version; test updates in staging before production |
| Monitoring/observability gaps prevent quick issue diagnosis | Medium | Medium | Comprehensive logging; Prometheus metrics; OpenTelemetry tracing; runbook documentation |

---

## 10. Target State (Post-Implementation)

### User Experience

**For End Users:**
- No visible changes; feature parity is 100%
- URL extraction may be slightly slower (network round-trip) but acceptable for fallback use case
- Card image generation latency similar (possibly slightly faster if services scale better)

**For Developers:**
- Faster local development cycle (API builds in <3 minutes without Playwright)
- Can develop API features without Playwright dependencies
- Can test API/Worker locally with fast builds
- Playwright service development isolated and independent

**For DevOps/Operations:**
- Smaller API and Worker images (faster deployments, less storage)
- Can scale Playwright services independently based on demand
- Browser failures isolated from API failures
- Clearer metrics and monitoring for browser automation
- More flexible resource allocation

### Technical Architecture

**Image Composition:**
- API Container: ~400-500MB (down from 1.71GB)
  - Base Python image + FastAPI + SQLAlchemy + core dependencies
  - NO Playwright, NO Chromium, NO browser system packages
  - Build time: <3 minutes

- Worker Container: ~400-500MB (down from 1.71GB)
  - Base Python image + Celery + Redis client + core dependencies
  - NO Playwright, NO Chromium, NO browser system packages
  - Build time: <3 minutes

- Playwright Ingestion Service: ~1.5GB (new, separate)
  - Base Python image + Playwright + browser system packages + Chromium
  - HTTP REST API server (FastAPI)
  - Browser pool management
  - Build time: <5 minutes

- Playwright Image Service: ~1.5GB (new, separate)
  - Base Python image + Playwright + browser system packages + Chromium
  - HTTP REST API server (FastAPI)
  - Browser pool management
  - Build time: <5 minutes

**Integration Points:**
- AdapterRouter calls Ingestion Service via HTTP instead of direct PlaywrightAdapter
- ImageGenerationService calls Image Service via HTTP instead of direct BrowserPool usage
- Both services discoverable via environment variables or service DNS names
- Both services emit OpenTelemetry spans and Prometheus metrics
- Both services have health check endpoints for orchestration

**Data Flow:**
- API/Worker remain stateless and lightweight
- Playwright services are stateful (browser pool state)
- All communication synchronous HTTP/REST (no message queue added)
- Graceful degradation if services unavailable (catch HTTP errors)

### Observable Outcomes

**Metrics Change:**
- Docker image size for API/Worker: 1.71GB → 400-500MB (60-70% reduction)
- Build time for API/Worker: 5-6 min → <3 min (50%+ reduction)
- Total system image size (3 containers): 5.13GB → 3.5-4GB (30% reduction)
- API memory footprint: ~200MB → ~150MB (baseline, no Playwright overhead)

**Behaviors Enabled:**
- Independent horizontal scaling of Playwright services
- Independent deployment of API/Worker from Playwright services
- Faster iteration cycles for core API development
- Better isolation of browser-related issues for troubleshooting

**Problems Solved:**
- Monolithic API container no longer carries 1.1GB of unused overhead in dev environments
- Cannot scale Playwright independently (problem solved by design)
- Browser failures no longer cascade to API failures (problem solved by design)
- Complex coupling between browser automation and core API (problem solved by design)

---

## 11. Overall Acceptance Criteria (Definition of Done)

### Functional Acceptance

- [ ] Playwright Ingestion Service API fully implements `/v1/extract` endpoint with request/response schema
- [ ] Playwright Image Service API fully implements `/v1/render` endpoint with request/response schema
- [ ] Both services implement `/health` and `/metrics` endpoints
- [ ] AdapterRouter successfully calls Ingestion Service and processes responses
- [ ] ImageGenerationService successfully calls Image Service and processes responses
- [ ] URL extraction success rate maintained at 85%+ (no regression)
- [ ] Card generation success rate maintained at 95%+ (no regression)
- [ ] All existing functionality works end-to-end without regressions

### Technical Acceptance

- [ ] API container builds without Playwright dependencies (<500MB, <3 min)
- [ ] Worker container builds without Playwright dependencies (<500MB, <3 min)
- [ ] Playwright Ingestion Service builds successfully with Playwright (~1.5GB, <5 min)
- [ ] Playwright Image Service builds successfully with Playwright (~1.5GB, <5 min)
- [ ] API/Worker Dockerfiles remove all Playwright system packages and imports
- [ ] Both Playwright services implement OpenTelemetry instrumentation
- [ ] Both Playwright services expose Prometheus metrics
- [ ] HTTP client in API/Worker implements retry logic and timeout handling
- [ ] Circuit breaker pattern prevents cascading failures
- [ ] Environment variable configuration for service endpoints

### Quality Acceptance

- [ ] Unit tests for new microservice endpoints: >80% coverage
- [ ] Integration tests for API/Worker → Playwright service communication
- [ ] End-to-end tests for complete workflows (import → extraction → creation)
- [ ] Performance tests validate latency targets (p95 <10s ingestion, <15s image)
- [ ] Load testing validates throughput targets (>100 concurrent ingestion, >50 concurrent render)
- [ ] Error handling tests cover timeout, crash, and invalid input scenarios
- [ ] Graceful degradation tests verify API/Worker work if services unavailable
- [ ] Docker Compose deployment tested and documented
- [ ] All tests pass with both development and production images
- [ ] No regression in extraction quality or rendering quality

### Documentation Acceptance

- [ ] Deployment guide for Docker Compose environments
- [ ] Architecture Decision Record (ADR) documenting microservice extraction rationale
- [ ] API documentation for both Playwright services (Swagger/OpenAPI)
- [ ] Configuration guide for environment variables
- [ ] Troubleshooting guide for common issues (browser crashes, timeouts, etc.)
- [ ] Runbook for production monitoring and incident response
- [ ] Changelog updated with breaking changes (none expected) and new capabilities

### Deployment Acceptance

- [ ] Zero-downtime deployment procedure documented and tested
- [ ] Rollback procedure documented and tested
- [ ] Monitoring/alerting configured for both services
- [ ] Health check endpoints validated
- [ ] Load balancer configuration (if applicable) documented
- [ ] Scaling procedures documented (horizontal scaling of services)

---

## 12. Assumptions & Open Questions

### Assumptions

- Network latency between API and Playwright services is negligible (<100ms) in production
- Docker Compose networking or equivalent private network available for internal communication
- No authentication/authorization needed between internal services (initial assumption)
- Playwright browser behavior and extraction logic remains unchanged in refactoring
- All browser automation use cases are covered by the two proposed services (no hidden dependencies)
- Current S3 caching strategy for images remains valid (not changing in this phase)
- Database models and schemas remain compatible (no schema changes needed)
- API and Worker deployments are independent (can be updated separately)

### Open Questions

- [ ] **Q1**: Should Playwright services be replicated/scaled horizontally in Docker Compose, or single instance per environment?
  - **A**: Initially single instance per environment, documented for scaling to multiple instances if needed

- [ ] **Q2**: Should Playwright services expose public APIs or remain internal only?
  - **A**: Internal only for now; no public API exposure; assume private network only

- [ ] **Q3**: How are Playwright service versions managed relative to API/Worker versions?
  - **A**: Independent versioning; services can be updated separately; document compatibility matrix

- [ ] **Q4**: Should extraction confidence score be returned in API responses?
  - **A**: Yes, include in response; can be used for UI quality indicators or post-processing filters

- [ ] **Q5**: What happens if image service is down for card generation—queue jobs or skip?
  - **A**: Skip generation, log warning; queuing introduced in future phase if needed

- [ ] **Q6**: Should browser pool size be configurable per environment?
  - **A**: Yes; environment variables for pool size; defaults to system resource constraints

- [ ] **Q7**: Do we need rate limiting or quota management for Playwright services?
  - **A**: Not in initial version; implement if abuse detected; future phase consideration

- [ ] **Q8**: Should extracted data be cached in Redis to reduce Playwright service load?
  - **A**: Future optimization; initial design assumes single extraction per URL

---

## 13. Implementation Phases

### Phase 1: Microservice Foundation (3-4 days)

**Objective:** Build and deploy Playwright services with baseline functionality

**Tasks:**
- [ ] Create Dockerfile for Playwright Ingestion Service (copy from existing API/Worker, add Playwright)
- [ ] Create Dockerfile for Playwright Image Service (copy from existing API/Worker, add Playwright)
- [ ] Implement FastAPI app for Ingestion Service with `/v1/extract` endpoint
- [ ] Implement FastAPI app for Image Service with `/v1/render` endpoint
- [ ] Implement HTTP health check endpoints (`/health`) for both services
- [ ] Implement Prometheus metrics endpoints (`/metrics`) for both services
- [ ] Add OpenTelemetry instrumentation to both services
- [ ] Create docker-compose.yml entries for both services
- [ ] Write comprehensive unit tests for both service endpoints
- [ ] Integration test: verify API can call services via HTTP
- [ ] Documentation: API specs, Docker build procedures, Docker Compose deployment

**Acceptance:**
- Both services build successfully and start in Docker Compose
- Health check endpoints return valid responses
- Metrics endpoints return Prometheus-format output
- Unit tests pass with >80% coverage
- Integration tests pass (API ↔ service communication works)

### Phase 2: API/Worker Refactoring (2-3 days)

**Objective:** Refactor API and Worker to use Playwright services instead of embedded functionality

**Tasks:**
- [ ] Create HTTP client wrapper for Ingestion Service in API (adapter/http_adapter.py)
- [ ] Create HTTP client wrapper for Image Service in API (services/http_image_generation.py)
- [ ] Update AdapterRouter to use HTTP client for Playwright fallback
- [ ] Update ImageGenerationService to call HTTP Image Service
- [ ] Remove PlaywrightAdapter and browser_pool.py imports from API/Worker
- [ ] Update Dockerfiles for API and Worker to remove Playwright dependencies
- [ ] Add environment variable configuration for service endpoints
- [ ] Implement circuit breaker pattern in HTTP clients
- [ ] Implement timeout handling (10s for ingestion, 15s for image)
- [ ] Write integration tests for API/Worker → service communication
- [ ] Write end-to-end tests for complete workflows
- [ ] Verify no Playwright imports remain in API/Worker code

**Acceptance:**
- API container builds without Playwright (<500MB, <3 min)
- Worker container builds without Playwright (<500MB, <3 min)
- All integration tests pass
- All end-to-end tests pass
- No regressions in extraction or rendering quality
- Docker Compose deployment works with all services

### Phase 3: Testing & Validation (2-3 days)

**Objective:** Comprehensive testing to ensure 100% functional parity and production readiness

**Tasks:**
- [ ] Performance testing: measure latency (p95, p99) for both services
- [ ] Load testing: validate throughput targets (>100 concurrent ingestion, >50 concurrent render)
- [ ] Stress testing: verify graceful degradation under load
- [ ] Error scenario testing: timeout, browser crash, invalid input, network failure
- [ ] Graceful degradation testing: API/Worker work if Playwright services unavailable
- [ ] Memory/resource usage testing: verify no leaks or excessive usage
- [ ] Extraction quality testing: validate against baseline (sample URLs)
- [ ] Rendering quality testing: validate against baseline (sample cards)
- [ ] Docker image size verification: confirm size reduction targets
- [ ] Build time verification: confirm build time reduction targets
- [ ] Runbook testing: document and test common operational procedures

**Acceptance:**
- All performance targets met (latency p95, throughput, memory)
- All error scenarios handled gracefully
- Extraction and rendering quality matches baseline
- Image sizes and build times meet targets
- Runbook procedures documented and tested

### Phase 4: Production Deployment & Monitoring (1-2 days)

**Objective:** Deploy to production with zero downtime and comprehensive monitoring

**Tasks:**
- [ ] Set up Prometheus monitoring for both Playwright services
- [ ] Set up alerting for service health, latency, error rate
- [ ] Configure load balancer (if applicable) for service discovery
- [ ] Document blue-green deployment procedure
- [ ] Document rollback procedure
- [ ] Perform staging deployment and validation
- [ ] Perform canary deployment to production (subset of traffic)
- [ ] Monitor metrics and error rates during canary phase
- [ ] Gradually increase traffic to Playwright services
- [ ] Decommission embedded Playwright code from API/Worker
- [ ] Update documentation and runbooks

**Acceptance:**
- Both services deployed and healthy in production
- Monitoring and alerting active
- Zero-downtime deployment completed successfully
- All metrics show expected values
- No regressions in production metrics
- Runbooks and playbooks documented and tested

---

## 14. Success Criteria & Metrics

### Technical Success Criteria

| Criterion | Target | Validation Method |
|-----------|--------|-------------------|
| API image size reduction | 1.71GB → <500MB | `docker images` output |
| Worker image size reduction | 1.71GB → <500MB | `docker images` output |
| API build time reduction | 5-6 min → <3 min | Build pipeline timing |
| Worker build time reduction | 5-6 min → <3 min | Build pipeline timing |
| Ingestion service latency (p95) | <10 seconds | Prometheus histogram |
| Image service latency (p95) | <15 seconds | Prometheus histogram |
| Ingestion service throughput | >100 concurrent | Load test results |
| Image service throughput | >50 concurrent | Load test results |
| Extraction success rate | ≥85% (baseline) | Test suite validation |
| Rendering success rate | ≥95% (baseline) | Test suite validation |
| Functional parity | 100% (no regressions) | Integration/E2E tests |
| Code coverage (new services) | >80% | Coverage report |

### Operational Success Criteria

| Criterion | Target | Validation Method |
|-----------|--------|-------------------|
| Service availability | 99.5% | Uptime monitoring |
| Mean time to recovery (browser crash) | <5 seconds | Incident metrics |
| Memory usage per service instance | <1GB | Container metrics |
| CPU usage under normal load | <50% of 1 core | Container metrics |
| Deployment downtime | 0 minutes | Blue-green deployment |
| Rollback time | <5 minutes | Procedure execution |
| Monitoring/alerting coverage | 100% of critical paths | Alert testing |

### Business Success Criteria

| Criterion | Target | Validation Method |
|-----------|--------|-------------------|
| Developer build time improvement | 50%+ reduction | Developer feedback |
| Deployment frequency | No degradation | CI/CD metrics |
| Production incident rate | No increase | Incident tracking |
| Feature velocity | No degradation | Sprint metrics |

---

## 15. Risk Assessment & Contingency

### High-Risk Areas

1. **Browser Stability:** Chromium crashes under load or with certain websites
   - Mitigation: Implement auto-recovery, monitoring, kill stale processes
   - Contingency: Add browser pool size limits, implement request queuing

2. **Network Latency:** Services in different containers cause response time increases
   - Mitigation: Docker Compose networking, measure baseline latency
   - Contingency: Cache extractions in Redis, implement circuit breaker

3. **Resource Exhaustion:** Memory/CPU limits prevent scaling
   - Mitigation: Monitor resource usage, set appropriate limits
   - Contingency: Implement horizontal scaling, add queue if needed

### Rollback Strategy

If critical issues discovered post-deployment:

1. **Immediate:** Route requests back to API-embedded Playwright code
2. **Short-term:** Redeploy old API/Worker images with embedded Playwright
3. **Permanent:** Evaluate root cause and decide: fix in services or return to monolith

Rollback time target: <10 minutes (via load balancer configuration)

---

## 16. Appendices & References

### Related Documentation

- **Architecture Analysis**: `/docs/architecture/playwright-optimization-analysis.md`
- **Docker Optimization Guide**: `/docs/development/docker-optimization.md`
- **Playwright Infrastructure PRD**: `/docs/project_plans/playwright-infrastructure/playwright-infrastructure-v1.md`
- **URL Ingestion Architecture**: `/docs/architecture/URL_INGESTION_ARCHITECTURE.md`

### Symbol References

**API Services:**
- `apps/api/dealbrain_api/services/image_generation.py` - ImageGenerationService (to refactor)
- `apps/api/dealbrain_api/adapters/` - Adapter implementations (to refactor)

**Frontend Components:**
- `apps/web/components/valuation/` - Card rendering components (related)
- `apps/web/app/dashboard/import/` - Import workflow (related)

### Key Files for Implementation

**Current Playwright Usage:**
- `apps/api/dealbrain_api/services/image_generation.py` (lines 131-655)
- `apps/api/dealbrain_api/tasks/card_images.py`
- `apps/api/dealbrain_api/adapters/browser_pool.py`
- `infra/api/Dockerfile` (lines 12-45, 56)
- `infra/worker/Dockerfile` (lines 12-45, 56)
- `pyproject.toml` (lines 47, 64-65)

**New Files to Create:**
- `apps/playwright-ingestion/` - New microservice
- `apps/playwright-image/` - New microservice
- `infra/ingestion/Dockerfile` - Service container
- `infra/image/Dockerfile` - Service container

### Testing Strategy

**Unit Tests:**
- Ingestion service endpoint logic (extraction, error handling)
- Image service endpoint logic (rendering, error handling)
- HTTP client retry logic and timeouts
- Circuit breaker pattern implementation

**Integration Tests:**
- API calls Ingestion Service successfully
- API handles Ingestion Service errors gracefully
- Worker calls Image Service successfully
- Worker handles Image Service errors gracefully
- Complete workflows (URL import, card generation) work end-to-end

**Performance Tests:**
- Latency percentiles (p50, p95, p99) for both services
- Throughput under load (concurrent requests)
- Resource usage (memory, CPU) over time

**Smoke Tests:**
- Services start successfully in Docker Compose
- Services respond to health checks
- Metrics endpoints return valid output
- Extraction quality matches baseline
- Rendering quality matches baseline

---

## Implementation Notes

### Key Decisions

1. **Two Separate Services (Not One):**
   - Decouples two independent use cases
   - Allows independent scaling based on demand
   - Isolation: image service failure doesn't affect URL extraction
   - Different performance characteristics (extract ~10s, render ~15s)

2. **HTTP/REST (Not gRPC or Queues):**
   - Simpler to implement and test
   - Standard monitoring/debugging tools work
   - Can be gradually replaced with gRPC/queues in future
   - Synchronous request/response matches current behavior

3. **Environment Variable Configuration:**
   - Simple to manage across environments
   - Works with Docker Compose and Kubernetes
   - No service discovery complexity initially

4. **Circuit Breaker Pattern:**
   - Prevents cascading failures
   - Allows services to gracefully degrade
   - Matches existing error handling patterns

### Implementation Order

1. Build services (Phase 1) - validate they work in isolation
2. Integrate with API/Worker (Phase 2) - validate system works together
3. Comprehensive testing (Phase 3) - ensure quality and parity
4. Production deployment (Phase 4) - gradual rollout with monitoring

### Success Definition

**The feature is complete when:**
- All functional requirements are met with zero regressions
- All non-functional requirements are met (latency, throughput, reliability)
- All acceptance criteria are checked off
- Production deployment successful with monitoring active
- Team comfortable supporting new architecture in production

---

**Progress Tracking:**

See progress tracking: `.claude/progress/playwright-microservice-extraction/all-phases-progress.md`

---

**Document Version:** 1.0
**Status:** Draft - Ready for Review
**Last Updated:** 2025-11-20
