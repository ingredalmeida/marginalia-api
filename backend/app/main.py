import asyncio
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from redis import Redis
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.health import router as health_router
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AuthError, ConflictError, DomainError, ForbiddenError, NotFoundError
from app.core.logging_config import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.core.rate_limit import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    log = structlog.get_logger(__name__)
    try:
        client = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=2,
        )
        await asyncio.to_thread(client.ping)
        app.state.redis = client
    except Exception as e:
        log.warning("redis_unavailable", error=str(e))
        app.state.redis = None
    yield
    r = getattr(app.state, "redis", None)
    if r is not None:
        try:
            await asyncio.to_thread(r.close)
        except Exception:
            pass


app = FastAPI(
    title="Marginalia Books API",
    description=(
        "REST API for library lending, catalog, and per-copy waitlists. "
        "Versioned resources are under **`/api/v1`**.\n\n"
        "**Auth:** create an account with **`POST /api/v1/auth/register`**, then obtain a JWT with "
        "**`POST /api/v1/auth/login`**. Other routes expect the header **`Authorization: Bearer`** plus that token, "
        "or use **Authorize** above. **`GET /health`**, **`GET /health/ready`**, this UI, "
        "and **`/openapi.json`** stay public.\n\n"
        "**Catalog staff:** creating or changing **authors** and **books** requires an **admin** user "
        "(`is_admin`). There is no HTTP endpoint to grant admin—configure that in your deployment (see README).\n\n"
        "Loan rules, fines, renewals, and waitlist behavior are described on each operation below. "
        "Due-date reminder emails run in a **background worker**, not through this HTTP API."
    ),
    version="0.7.0",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "Auth",
            "description": (
                "Patron self-service: `POST /auth/register` (name, email, password) returns `UserRead`; "
                "`POST /auth/login` returns `access_token`. Rate-limited per IP. No JWT required here."
            ),
        },
        {
            "name": "Users",
            "description": (
                "List/get users; `PATCH` profile (self or admin); `DELETE` user (admin only). "
                "`GET /users/{id}/loans` for loan history with filters."
            ),
        },
        {
            "name": "Authors",
            "description": (
                "Author CRUD. **Write** operations (`POST`, `PATCH`, `DELETE`) require **admin** JWT."
            ),
        },
        {
            "name": "Books",
            "description": (
                "Catalog CRUD and availability. **Write** requires **admin**. Responses may be Redis-cached."
            ),
        },
        {
            "name": "Loans",
            "description": (
                "Borrow (`POST /loans`, default **14-day** term), return, renew once (+4 days, rules apply), "
                "list with `filter`. Waitlist rules apply when creating a loan."
            ),
        },
        {
            "name": "Reservations",
            "description": (
                "Per-copy waitlist while the copy is on loan: create, list (by book or self), cancel. FIFO order."
            ),
        },
        {
            "name": "Health",
            "description": (
                "`GET /health` and **`GET /health/live`** — liveness. **`GET /health/ready`** — PostgreSQL required; "
                "Redis/cache optional (may report `degraded`). No JWT."
            ),
        },
        {
            "name": "Reports",
            "description": (
                "**Admin only:** CSV/PDF exports (`GET /api/v1/reports/*`). Operational snapshots for staff; "
                "in larger orgs the same data would feed an **ETL → warehouse → BI** (e.g. Power BI)."
            ),
        },
        {
            "name": "Admin",
            "description": (
                "**Admin only:** JSON agregado para o painel (`GET /api/v1/admin/dashboard`). "
                "Exportações detalhadas continuam em **Reports**."
            ),
        },
    ],
)

app.state.limiter = limiter
if settings.cors_origins_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(RequestContextMiddleware)
app.include_router(api_router)
app.include_router(health_router)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})["HTTPBearer"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "JWT from `POST /api/v1/auth/login`. Use **Authorize** to attach it to requests.",
    }
    openapi_schema["servers"] = [
        {
            "url": "http://localhost:8000",
            "description": "Local default (e.g. `docker compose up`)",
        },
    ]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

_error_log = structlog.get_logger("api.client_error")


@app.exception_handler(NotFoundError)
def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    _error_log.warning(
        "client_error",
        correlation_id=getattr(request.state, "correlation_id", None),
        status_code=404,
        detail=str(exc),
    )
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ConflictError)
def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
    _error_log.warning(
        "client_error",
        correlation_id=getattr(request.state, "correlation_id", None),
        status_code=409,
        detail=str(exc),
    )
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(DomainError)
def domain_handler(request: Request, exc: DomainError) -> JSONResponse:
    _error_log.warning(
        "client_error",
        correlation_id=getattr(request.state, "correlation_id", None),
        status_code=400,
        detail=str(exc),
    )
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(ForbiddenError)
def forbidden_handler(request: Request, exc: ForbiddenError) -> JSONResponse:
    _error_log.warning(
        "client_error",
        correlation_id=getattr(request.state, "correlation_id", None),
        status_code=403,
        detail=str(exc),
    )
    return JSONResponse(status_code=403, content={"detail": str(exc)})


@app.exception_handler(AuthError)
def auth_handler(request: Request, exc: AuthError) -> JSONResponse:
    _error_log.warning(
        "client_error",
        correlation_id=getattr(request.state, "correlation_id", None),
        status_code=401,
        detail=str(exc),
    )
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc)},
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(RequestValidationError)
def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    _error_log.warning(
        "validation_error",
        correlation_id=getattr(request.state, "correlation_id", None),
        status_code=422,
        error_count=len(errors),
    )
    return JSONResponse(status_code=422, content={"detail": errors})
