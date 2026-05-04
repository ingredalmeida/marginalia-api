"""Estimated fine for an active loan if returned now (same rule as return_loan)."""

from datetime import datetime, timezone
from decimal import Decimal

from app.core.constants import FINE_PER_OVERDUE_DAY


def projected_fine_if_returned_now(
    due_at: datetime,
    *,
    returned_at: datetime | None,
    as_of: datetime | None = None,
) -> Decimal | None:
    """None if already returned (use stored fine_amount). Else estimated BRL."""
    if returned_at is not None:
        return None
    due = due_at if due_at.tzinfo else due_at.replace(tzinfo=timezone.utc)
    now = as_of if as_of is not None else datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    due_date = due.date()
    charge_date = now.date()
    overdue_days = max(0, (charge_date - due_date).days)
    return Decimal(overdue_days) * FINE_PER_OVERDUE_DAY
