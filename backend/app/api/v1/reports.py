"""Admin-only report exports (CSV/PDF)."""

from datetime import date, datetime, timezone
from io import BytesIO
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_db
from app.core.reporting_period import resolve_report_period
from app.models import User
from app.schemas.report import ReportFormat
from app.services import report_service
from app.services.report_render import chart_bar, iter_csv_rows, to_pdf

router = APIRouter(prefix="/reports", tags=["Reports"])

LOANS_HEADERS = [
    "loan_id",
    "user_email",
    "user_name",
    "book_title",
    "author_name",
    "borrowed_at",
    "due_at",
    "returned_at",
    "fine_amount",
    "status",
]

FINES_DETAIL_HEADERS = [
    "loan_id",
    "user_email",
    "user_name",
    "book_title",
    "returned_at",
    "fine_amount_brl",
]

TOP_BOOKS_HEADERS = ["book_id", "title", "author_name", "loan_count"]

INVENTORY_HEADERS = ["book_id", "title", "author_name", "isbn", "publication_year", "available"]


def _disposition(base: str, ext: str) -> str:
    return f'attachment; filename="{base}.{ext}"'


@router.get("/loans")
async def report_loans(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
    date_from: Annotated[
        date | None,
        Query(description="Start date inclusive (UTC). Default: 30 days before date_to."),
    ] = None,
    date_to: Annotated[
        date | None,
        Query(description="End date inclusive (UTC). Default: today (UTC)."),
    ] = None,
    report_format: Annotated[ReportFormat, Query(alias="format")] = ReportFormat.csv,
) -> StreamingResponse:
    """Loans whose borrowed_at falls in the period."""
    d0, d1 = resolve_report_period(date_from, date_to)
    rows = await report_service.loans_in_period(db, d0, d1)
    base = f"loans_{d0.isoformat()}_{d1.isoformat()}"
    subtitle = f"Period (UTC): {d0.isoformat()} — {d1.isoformat()} · rows: {len(rows)}"

    if report_format == ReportFormat.csv:
        return StreamingResponse(
            iter_csv_rows(rows, LOANS_HEADERS),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": _disposition(base, "csv")},
        )
    pdf = to_pdf("Loans report", subtitle, rows, LOANS_HEADERS, chart_png=None)
    return StreamingResponse(
        BytesIO(pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": _disposition(base, "pdf")},
    )


@router.get("/fines")
async def report_fines(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
    report_format: Annotated[ReportFormat, Query(alias="format")] = ReportFormat.csv,
) -> StreamingResponse:
    """Returned loans with fines in the period (by returned_at)."""
    d0, d1 = resolve_report_period(date_from, date_to)
    detail, aggregates = await report_service.fines_in_period(db, d0, d1)
    base = f"fines_{d0.isoformat()}_{d1.isoformat()}"
    subtitle = f"Period (UTC): {d0.isoformat()} — {d1.isoformat()} · detail rows: {len(detail)}"

    if report_format == ReportFormat.csv:
        return StreamingResponse(
            iter_csv_rows(detail, FINES_DETAIL_HEADERS),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": _disposition(base, "csv")},
        )

    chart_png: bytes | None = None
    if aggregates:
        labels = [str(a["user_email"]) for a in aggregates[:15]]
        values = [float(str(a["total_fine_brl"])) for a in aggregates[:15]]
        chart_png = chart_bar(labels, values, "Total fines by patron (top 15)")
    pdf = to_pdf("Fines report", subtitle, detail, FINES_DETAIL_HEADERS, chart_png=chart_png)
    return StreamingResponse(
        BytesIO(pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": _disposition(base, "pdf")},
    )


@router.get("/top-books")
async def report_top_books(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    report_format: Annotated[ReportFormat, Query(alias="format")] = ReportFormat.csv,
) -> StreamingResponse:
    """Most borrowed books in the period (by borrowed_at)."""
    d0, d1 = resolve_report_period(date_from, date_to)
    rows = await report_service.top_books_in_period(db, d0, d1, limit)
    base = f"top_books_{d0.isoformat()}_{d1.isoformat()}"
    subtitle = f"Period (UTC): {d0.isoformat()} — {d1.isoformat()} · limit: {limit}"

    if report_format == ReportFormat.csv:
        return StreamingResponse(
            iter_csv_rows(rows, TOP_BOOKS_HEADERS),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": _disposition(base, "csv")},
        )

    chart_png: bytes | None = None
    if rows:
        labels = [str(r["title"]) for r in rows]
        values = [float(r["loan_count"]) for r in rows]
        chart_png = chart_bar(labels, values, "Loan count by book")
    pdf = to_pdf("Top books report", subtitle, rows, TOP_BOOKS_HEADERS, chart_png=chart_png)
    return StreamingResponse(
        BytesIO(pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": _disposition(base, "pdf")},
    )


@router.get("/inventory")
async def report_inventory(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
    report_format: Annotated[ReportFormat, Query(alias="format")] = ReportFormat.csv,
) -> StreamingResponse:
    """Full catalog snapshot with availability (one active loan per copy model)."""
    rows = await report_service.inventory_snapshot(db)
    today = datetime.now(timezone.utc).date().isoformat()
    base = f"inventory_{today}"
    subtitle = f"Generated (UTC date): {today} · titles: {len(rows)}"

    if report_format == ReportFormat.csv:
        return StreamingResponse(
            iter_csv_rows(rows, INVENTORY_HEADERS),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": _disposition(base, "csv")},
        )

    avail = sum(1 for r in rows if r.get("available") == "yes")
    on_loan = len(rows) - avail
    chart_png = chart_bar(
        ["Available", "On loan"],
        [float(avail), float(on_loan)],
        "Copies available vs on loan",
    )
    pdf = to_pdf("Inventory report", subtitle, rows, INVENTORY_HEADERS, chart_png=chart_png)
    return StreamingResponse(
        BytesIO(pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": _disposition(base, "pdf")},
    )
