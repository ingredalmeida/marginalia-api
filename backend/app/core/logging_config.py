import logging
import sys

import structlog

from app.core.config import settings


def configure_logging() -> None:
    """Configure structlog for structured JSON or console output."""
    shared: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    if settings.log_format == "json":
        processors: list[structlog.types.Processor] = [*shared, structlog.processors.JSONRenderer()]
    else:
        processors = [*shared, structlog.dev.ConsoleRenderer()]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    # keep uvicorn access noise down
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
