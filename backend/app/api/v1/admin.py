"""Rotas admin só para JSON (dashboard); relatórios CSV/PDF em ``/reports``."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_db
from app.core.reporting_period import resolve_report_period
from app.models import User
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard_service import dashboard_summary

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard", response_model=DashboardSummary)
async def admin_dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
    date_from: Annotated[
        date | None,
        Query(description="Início do período (UTC). Padrão: 30 dias antes de date_to."),
    ] = None,
    date_to: Annotated[
        date | None,
        Query(description="Fim do período inclusive (UTC). Padrão: hoje (UTC)."),
    ] = None,
) -> DashboardSummary:
    d0, d1 = resolve_report_period(date_from, date_to)
    return await dashboard_summary(db, d0, d1)
