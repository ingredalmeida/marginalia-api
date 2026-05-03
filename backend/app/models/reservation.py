from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Reservation(Base):
    """Waitlist for a single copy (`book_id`). FIFO by `created_at`, then `id`."""

    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    hold_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    user: Mapped["User"] = relationship("User", back_populates="reservations")
    book: Mapped["Book"] = relationship("Book", back_populates="reservations")
