import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Assigns a per-request correlation id (header X-Correlation-ID or generated UUID),
    stores it on request.state for sync route handlers, logs a structured access line,
    and echoes the id on the response.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        start = time.perf_counter()
        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start) * 1000, 3)
            structlog.get_logger("http").info(
                "request_completed",
                correlation_id=correlation_id,
                http_method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
            )
            response.headers["X-Correlation-ID"] = correlation_id
            return response
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000, 3)
            structlog.get_logger("http").exception(
                "request_failed",
                correlation_id=correlation_id,
                http_method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
            )
            raise
