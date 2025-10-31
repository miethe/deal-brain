"""Core telemetry bootstrap utilities."""

from __future__ import annotations

import logging
import sys
from logging import config as logging_config
from typing import Iterable

import structlog
from dealbrain_api.settings import Settings, TelemetrySettings

_CONFIGURED = False


def _build_pre_chain(environment: str, service_name: str) -> list[structlog.types.Processor]:
    """Processors that run prior to rendering."""

    def add_environment(
        _logger: logging.Logger, _name: str, event_dict: structlog.types.EventDict
    ) -> structlog.types.EventDict:
        if "environment" not in event_dict:
            event_dict["environment"] = environment
        return event_dict

    def add_service(
        _logger: logging.Logger, _name: str, event_dict: structlog.types.EventDict
    ) -> structlog.types.EventDict:
        if "service" not in event_dict:
            event_dict["service"] = service_name
        return event_dict

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    return [
        structlog.contextvars.merge_contextvars,
        add_service,
        add_environment,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        timestamper,
    ]


def _configure_structlog(
    pre_chain: Iterable[structlog.types.Processor], renderer: structlog.types.Processor, level: str
) -> None:
    """Configure structlog to work alongside the standard logging module."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging_config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "structlog": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": renderer,
                    "foreign_pre_chain": list(pre_chain),
                },
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "structlog",
                    "stream": sys.stdout,
                }
            },
            "loggers": {
                "": {"handlers": ["default"], "level": level, "propagate": False},
                "uvicorn.error": {"handlers": ["default"], "level": level, "propagate": False},
                "uvicorn.access": {"handlers": ["default"], "level": level, "propagate": False},
            },
        }
    )


def _setup_otlp_logging(telemetry: TelemetrySettings, level: str) -> None:
    """Configure OpenTelemetry log exporter handler if available."""
    try:
        from opentelemetry._logs import set_logger_provider
        from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
        from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
        from opentelemetry.sdk.resources import Resource
    except ImportError:  # pragma: no cover - optional dependency
        logging.getLogger("dealbrain.telemetry").warning(
            "opentelemetry dependencies missing; falling back to stdout logging"
        )
        return

    if not telemetry.otel_endpoint:
        logging.getLogger("dealbrain.telemetry").warning(
            "OTLP log exporter selected but no endpoint configured; skipping remote export"
        )
        return

    resource = Resource.create({"service.name": telemetry.service_name})
    provider = LoggerProvider(resource=resource)
    exporter = OTLPLogExporter(endpoint=telemetry.otel_endpoint, insecure=True)
    provider.add_log_record_processor(BatchLogRecordProcessor(exporter))

    handler = LoggingHandler(level=level, logger_provider=provider)
    set_logger_provider(provider)

    logging.getLogger().addHandler(handler)


def _configure_tracing(telemetry: TelemetrySettings) -> None:
    """Initialize OpenTelemetry tracing pipeline when enabled."""
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:  # pragma: no cover - optional dependency
        logging.getLogger("dealbrain.telemetry").warning(
            "Unable to enable tracing; opentelemetry exporter not installed"
        )
        return

    if not telemetry.otel_endpoint:
        logging.getLogger("dealbrain.telemetry").warning(
            "Tracing requested but no OTLP endpoint configured; skipping tracer initialization"
        )
        return

    resource = Resource.create({"service.name": telemetry.service_name})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=telemetry.otel_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


def init_telemetry(settings: Settings) -> None:
    """Initialise logging and tracing according to settings."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    telemetry = settings.telemetry
    log_level = telemetry.level or settings.log_level

    renderer: structlog.types.Processor
    if telemetry.destination == "console" and telemetry.log_format == "console":
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    else:
        renderer = structlog.processors.JSONRenderer()

    pre_chain = _build_pre_chain(
        environment=settings.environment, service_name=telemetry.service_name
    )
    _configure_structlog(pre_chain, renderer, log_level)

    logging.root.setLevel(log_level)
    logging.getLogger("uvicorn.error").setLevel(log_level)
    if telemetry.suppress_uvicorn_access:
        logging.getLogger("uvicorn.access").setLevel("WARNING")
    else:
        logging.getLogger("uvicorn.access").setLevel(log_level)

    if telemetry.destination == "otel":
        _setup_otlp_logging(telemetry, log_level)

    if telemetry.enable_tracing:
        _configure_tracing(telemetry)

    structlog.get_logger("dealbrain.telemetry").info(
        "telemetry.initialized",
        destination=telemetry.destination,
        level=log_level,
        tracing_enabled=telemetry.enable_tracing,
    )

    _CONFIGURED = True


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Convenience helper mirroring logging.getLogger."""
    return structlog.get_logger(name)
