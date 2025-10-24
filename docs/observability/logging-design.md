# Observability & Logging Design

## Objectives
- Provide a consistent logging and telemetry solution across the Deal Brain backend (FastAPI, Celery, CLI) and the Next.js frontend.
- Ship a solution that works out-of-the-box for local development (console logging) and can be switched to structured production logging or remote exporters via configuration flags.
- Capture request-level context (request id, user id when available) and task/job identifiers to make debugging and incident response faster.
- Ensure the implementation is lightweight, keeps dependencies minimal, and fits with existing Prometheus metrics collection.

## Requirements
- **Destinations**: Console (development), JSON/stdout (production), OTLP/OTel collector (optional). Prometheus metrics already exist for FastAPI; we will keep those and emit new telemetry counters/timers where it adds value.
- **Configuration**: Controlled through Pydantic settings on the backend (`TelemetrySettings`) and environment variables on the frontend (`NEXT_PUBLIC_TELEMETRY_DESTINATION`, `NEXT_PUBLIC_TELEMETRY_ENDPOINT`).
- **Structure**: All logs should include level, event name, message, timestamp, environment, and contextual fields (request_id, user_id, task_id, etc.).
- **Framework integration**:
  - FastAPI: startup hook initializes telemetry; middleware emits structured request spans and attaches context vars.
  - Celery: signal handlers initialize telemetry per worker and capture task lifecycle logs.
  - CLI: initialize telemetry before executing commands.
  - Frontend: client-side telemetry helper centralizes logging, forwards to `console` in development, and optionally POSTs to `/api/telemetry/logs` (new endpoint) or a remote collector.
- **Extensibility**: Easy to add new exporters (e.g., Datadog, Splunk) by extending a factory that builds logging handlers.

## Proposed Architecture

### Backend Logging Stack
1. **`dealbrain_api.telemetry` module** (new)
   - `TelemetrySettings`: Pydantic model with fields for `log_level`, `log_destination`, `log_format`, `otel_endpoint`, and `enable_tracing`.
   - `configure_logging(settings)`: applies Python `logging` configuration and `structlog` processors.
   - `configure_tracing(settings)`: optionally boots OpenTelemetry tracing (OTLP).
   - `RequestContext` utilities that use `contextvars` to store request ids and surface them via a `structlog` processor.
   - `FastAPI` middleware (`ObservabilityMiddleware`) that emits request logs (method, path, status, latency, trace id) and ensures each request has a correlation id.
   - `get_logger(name=None)`: convenience wrapper around `structlog.get_logger`.

2. **Handlers / Destinations**
   - `console`: colored human-readable logs (for development).
   - `json`: JSON structured logs to stdout (for production).
   - `otel`: uses `opentelemetry-sdk` log handler to export to OTLP endpoint (configurable). Falls back gracefully if package/env missing.

3. **Instrumentation Targets (initial rollout)**
   - App startup/shutdown events.
   - API request middleware.
   - High-traffic services: `services/listings.py`, `services/ingestion.py`, `services/rule_evaluation.py`, and shared rules engine in `packages/core/dealbrain_core/rules`.
   - Celery tasks in `apps/api/dealbrain_api/tasks`.
   - CLI command entrypoints.

4. **Context Propagation**
   - Middleware generates `request_id` stored in `contextvars`.
   - Celery tasks include `task_id`.
   - Services accept optional `TelemetryContext` (dict) that can be enriched (e.g., `listing_id`, `ruleset_id`).

5. **Metrics & Tracing**
   - Keep existing Prometheus instrumentation.
   - Provide helper to emit counters (wrapping `prometheus_client`) where useful (e.g., ingestion attempts, rule evaluation errors).
   - Optional OTLP tracing: create `TracerProvider` with `BatchSpanProcessor` and `OTLPSpanExporter`.

### Frontend Telemetry
1. **`apps/web/lib/telemetry.ts`** (new)
   - `createTelemetryClient` returns an object with `info`, `warn`, `error`, and `trackEvent`.
   - Respects environment variables:
     - `NEXT_PUBLIC_TELEMETRY_DESTINATION=console|endpoint|disabled`
     - `NEXT_PUBLIC_TELEMETRY_ENDPOINT=https://…` (defaults to `/api/telemetry/logs`)
   - Uses `console` in development unless explicitly disabled.
   - Sends logs/events via `navigator.sendBeacon` (preferred) or `fetch`.
   - Automatically attaches `sessionId` (from `localStorage`) and optional `user` context when available.

2. **React Integration**
   - Provide `TelemetryProvider` (React context) and `useTelemetry` hook for components.
   - Wrap global layout to ensure errors reported through `ErrorBoundary` go through telemetry client.
   - Replace ad-hoc `console.*` calls with telemetry client usage in high-traffic modules (`import` flow, ingestion components, global errors).

3. **Backend endpoint for frontend logs**
   - `POST /telemetry/logs` FastAPI route receives frontend logs, validates payload, and re-emits using backend logger (with `source=frontend`).

### Configuration & Deployment
- New environment variables:
  - Backend: `DEALBRAIN_LOG_DESTINATION`, `DEALBRAIN_LOG_LEVEL`, `DEALBRAIN_OTEL_ENDPOINT`, `DEALBRAIN_ENABLE_TRACING`.
  - Frontend: `NEXT_PUBLIC_TELEMETRY_DESTINATION`, `NEXT_PUBLIC_TELEMETRY_ENDPOINT`.
- Defaults favour console logging in development and JSON logs in production.
- Documented in a new developer guide: `docs/observability/developer-guide.md`.

## Implementation Plan
1. Add telemetry settings models and helper module (`dealbrain_api/telemetry`).
2. Initialize telemetry during FastAPI startup and in CLI/Celery entrypoints.
3. Add request middleware and context utilities; instrument key services.
4. Add OTLP exporter support and graceful fallback when libs not installed.
5. Implement frontend telemetry client and replace critical `console.*` calls.
6. Introduce `POST /telemetry/logs` endpoint to aggregate frontend events.
7. Write developer guide with configuration examples and coding guidelines.

