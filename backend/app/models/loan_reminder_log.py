from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class LoanReminderLog(Base):
    """Tracks sent due reminders per loan + due calendar date + kind (idempotency)."""

    __tablename__ = "loan_reminder_logs"
    __table_args__ = (
        UniqueConstraint(
            "loan_id",
            "due_date",
            "reminder_kind",
            name="uq_loan_reminder_log_loan_due_kind",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    loan_id: Mapped[int] = mapped_column(ForeignKey("loans.id"), nullable=False, index=True)
    due_date: Mapped[date] = mapped_column(Date(), nullable=False)
    reminder_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    email_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    webhook_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    loan: Mapped["Loan"] = relationship("Loan", back_populates="reminder_logs")
