from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Book(Base):
    __tablename__ = "books"
    __table_args__ = (UniqueConstraint("isbn", name="uq_books_isbn"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    isbn: Mapped[str | None] = mapped_column(String(32), nullable=True)
    publication_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    author: Mapped["Author"] = relationship("Author", back_populates="books")
    loans: Mapped[list["Loan"]] = relationship("Loan", back_populates="book")
    reservations: Mapped[list["Reservation"]] = relationship(
        "Reservation", back_populates="book"
    )
