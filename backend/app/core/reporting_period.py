"""Intervalo de datas padrão dos relatórios (alinhado ao admin dashboard)."""

from datetime import date, datetime, timedelta, timezone

from app.core.exceptions import DomainError


def resolve_report_period(
    date_from: date | None,
    date_to: date | None,
) -> tuple[date, date]:
    if date_to is None:
        date_to = datetime.now(timezone.utc).date()
    if date_from is None:
        date_from = date_to - timedelta(days=30)
    if date_to < date_from:
        raise DomainError("date_to must be greater than or equal to date_from.")
    return date_from, date_to
