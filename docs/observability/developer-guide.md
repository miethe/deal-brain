# Observability Developer Guide

This guide explains how to instrument new code with the Deal Brain observability stack. The tooling covers backend services (FastAPI, Celery, CLI) and the Next.js frontend.

## Quick Start
- **Backend logging:** `from dealbrain_api.telemetry import get_logger` then emit events such as `logger.info("rules.evaluate.success", listing_id=listing.id)`.
- **Frontend logging:** `import { telemetry } from '@/lib/telemetry'` and call `telemetry.info("component.event", { ... })`.
- **Configuration:** controlled via environment variables (`TELEMETRY__DESTINATION`, `NEXT_PUBLIC_TELEMETRY_DESTINATION`, etc.). Defaults favor console logging in development and JSON logs in production.

## Backend Instrumentation
### Telemetry settings
`dealbrain_api.settings.Settings` exposes a nested `telemetry` configuration. Key environment variables:
- `TELEMETRY__DESTINATION`: `console` (default), `json`, or `otel`.
- `TELEMETRY__LEVEL`: Log level (`INFO` default).
- `TELEMETRY__LOG_FORMAT`: `console` (dev-friendly) or `json`.
- `TELEMETRY__OTEL_ENDPOINT`: OTLP collector endpoint (e.g. `http://otel-collector:4317`).
- `TELEMETRY__ENABLE_TRACING`: `true` to emit OpenTelemetry spans to the OTLP endpoint.

The FastAPI app, Celery worker, and CLI initialise telemetry automatically via `dealbrain_api.telemetry.init_telemetry`.

### Logging APIs
- Prefer `get_logger("dealbrain.component")` to create a structured logger.
- Emit event-oriented messages (`logger.info("ingestion.url.completed", url=url, status=status)`).
- Request context such as `request_id` is automatically injected by `ObservabilityMiddleware`. For Celery tasks or utilities, bind additional context via `from dealbrain_api.telemetry import bind_request_context, clear_context`.
- Use structured key/value arguments instead of string interpolation; everything is serialized to JSON (and to OTLP when enabled).

### Adding telemetry to async tasks
- Celery tasks already bind correlation IDs, but new async helpers should call `bind_request_context(new_request_id(), task="my.task")` at entry and `clear_context()` in `finally`.
- When adding Prometheus metrics, coordinate with the existing counters in `services/rule_evaluation.py` to maintain naming consistency.

## Frontend Instrumentation
### Telemetry client
`apps/web/lib/telemetry.ts` exposes a singleton `telemetry` with `debug`, `info`, `warn`, and `error` methods. All calls include:
- ISO timestamp
- Session ID (persisted in localStorage)
- Optional payload and user context

Usage example:
```tsx
import { telemetry } from "@/lib/telemetry";

telemetry.info("frontend.import.success", { listingId, provenance });
telemetry.error("frontend.form.submit_failed", { message: error.message });
```

### Configuration
- `NEXT_PUBLIC_TELEMETRY_DESTINATION`: `console` (default), `endpoint`, `all`, or `disabled`.
- `NEXT_PUBLIC_TELEMETRY_ENDPOINT`: REST endpoint for log ingestion (`/api/telemetry/logs` by default).

When `endpoint` or `all` is selected, the client uses `navigator.sendBeacon` (with fetch fallback) to POST events to the API.

### Error handling and analytics
- `components/error-boundary.tsx` forwards caught errors to telemetry; reuse `telemetry` in new error boundaries or hooks.
- `lib/analytics.ts` now forwards `track()` calls to telemetry—custom analytics should use event names under the `analytics.*` prefix.

## Telemetry API Endpoint
- `POST /telemetry/logs` accepts payloads conforming to `TelemetryLogEntry` and re-emits them through backend logging.
- Event fields: `level`, `event`, `payload`, `session_id`, optional `user`.
- Responses return HTTP 202 on success; failures are logged server-side.

## OpenTelemetry Support
- Set `TELEMETRY__DESTINATION=otel`, `TELEMETRY__OTEL_ENDPOINT=http://collector:4317`, and enable tracing to stream logs and spans to your collector.
- Logs use the OTLP gRPC exporter. Traces are emitted via `opentelemetry-sdk` with a `BatchSpanProcessor`.
- Ensure the OTLP collector allows insecure connections if using `http://`; configure TLS by supplying `https://` endpoints.

## Coding Guidelines
1. **Event names**: follow `domain.action.outcome` (e.g. `ingestion.url.failed`, `valuation.recalc.complete`).
2. **Context richness**: include identifiers (`listing_id`, `job_id`), status flags, and magnitudes (`duration_ms`, `total_adjustment`). Avoid embedding free-form strings when structured fields are available.
3. **Avoid noisy loops**: throttle or guard high-frequency logging—use `debug` level for granular iterations (e.g., ingestion progress updates only in development).
4. **Error handling**: `logger.exception(...)` automatically records stack traces; add contextual fields alongside the exception when helpful.
5. **Frontend parity**: mirror event names between frontend telemetry and backend logs to ease correlation.

## Troubleshooting
- **No logs appearing**: verify `TELEMETRY__DESTINATION` is set (default `console`), and ensure initialization runs before logging (e.g., call `init_telemetry(get_settings())` in new entrypoints).
- **OTLP failures**: when enabling OTLP, check collector reachability. The setup logs a warning and falls back to stdout if dependencies or endpoints are missing.
- **Frontend endpoint 404**: confirm the API router includes `telemetry.router` (already wired in `api/__init__.py`) and that the frontend points to the correct base path.

## Reference Implementation
- `services/listings.py`: structured lifecycle logging for creations, updates, and metric recomputations.
- `services/ingestion.py`: dedup telemetry, CPU matching diagnostics, and ingestion orchestration events.
- `tasks/ingestion.py` / `tasks/valuation.py`: Celery task logs with correlation IDs and progress milestones.
- `lib/telemetry.ts`: browser client that switches destinations by configuration.

Follow these patterns when extending observability to new modules or features.

