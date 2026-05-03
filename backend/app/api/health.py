import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db

router = APIRouter(tags=["Health"])

_DB_CHECK_TIMEOUT_S = 1.0
_REDIS_CHECK_TIMEOUT_S = 1.0


@router.get("/health")
async def health() -> dict:
    """Liveness: process is up (use for simple probes)."""
    return {"status": "ok"}


@router.get("/health/live")
async def health_live() -> dict:
    """Explicit liveness alias."""
    return {"status": "ok"}


@router.get("/health/ready")
async def health_ready(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JSONResponse:
    """
    Readiness: PostgreSQL required (503 if down). Redis optional — cache degraded but HTTP 200.
    """
    checks: dict[str, str] = {}

    try:
        await asyncio.wait_for(db.execute(text("SELECT 1")), timeout=_DB_CHECK_TIMEOUT_S)
        checks["db"] = "ok"
    except Exception:
        checks["db"] = "down"
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "checks": checks},
        )

    redis_client = getattr(request.app.state, "redis", None)
    overall = "ready"

    if redis_client is None:
        checks["redis"] = "disabled"
        checks["cache"] = "disabled"
    else:
        try:
            await asyncio.wait_for(
                asyncio.to_thread(redis_client.ping),
                timeout=_REDIS_CHECK_TIMEOUT_S,
            )
            checks["redis"] = "ok"
            checks["cache"] = "enabled"
        except Exception:
            checks["redis"] = "down"
            checks["cache"] = "enabled"
            overall = "degraded"

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": overall, "checks": checks},
    )
