from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False, index=True)
    borrowed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    renewal_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", default=0)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fine_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="loans")
    book: Mapped["Book"] = relationship("Book", back_populates="loans")
    reminder_logs: Mapped[list["LoanReminderLog"]] = relationship(
        "LoanReminderLog", back_populates="loan"
    )
