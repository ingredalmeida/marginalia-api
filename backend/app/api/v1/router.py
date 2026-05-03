from fastapi import APIRouter, Depends

from app.api.deps import bind_correlation_context, get_current_user
from app.api.v1 import admin, auth, authors, books, loans, notifications, reports, reservations, users
from app.schemas.errors import ErrorResponse

api_router = APIRouter(
    prefix="/api/v1",
    dependencies=[Depends(bind_correlation_context)],
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Business rule violation (e.g. returning an already returned loan).",
        },
        401: {
            "model": ErrorResponse,
            "description": "Missing or invalid JWT (use `Authorization: Bearer <token>`).",
        },
        403: {
            "model": ErrorResponse,
            "description": "Authenticated but not allowed (e.g. catalog write/delete requires `is_admin`).",
        },
        404: {
            "model": ErrorResponse,
            "description": "Resource not found.",
        },
        409: {
            "model": ErrorResponse,
            "description": "Conflict with current state (e.g. loan limit, book already borrowed).",
        },
        422: {
            "description": "Validation error: request body or query does not match the schema.",
        },
    },
)

api_router.include_router(auth.router)

protected = APIRouter(dependencies=[Depends(get_current_user)])
protected.include_router(users.router)
protected.include_router(authors.router)
protected.include_router(books.router)
protected.include_router(loans.router)
protected.include_router(notifications.router)
protected.include_router(reservations.router)
protected.include_router(reports.router)
protected.include_router(admin.router)
api_router.include_router(protected)
