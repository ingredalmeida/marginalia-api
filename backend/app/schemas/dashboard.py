from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class TopBookItem(BaseModel):
    book_id: int
    title: str
    author_name: str
    loan_count: int


class DashboardSummary(BaseModel):
    date_from: date
    date_to: date
    book_titles_total: int = Field(description="Títulos cadastrados no acervo")
    users_total: int
    active_loans: int = Field(description="Empréstimos ainda não devolvidos")
    overdue_loans: int = Field(description="Entre os ativos, com data de devolução já passada")
    loans_started_in_period: int = Field(description="Novos empréstimos com retirada no período")
    total_fines_brl: str = Field(description="Soma de multas (devoluções com multa no período)")
    available_titles: int = Field(description="Títulos sem exemplar emprestado agora")
    on_loan_titles: int = Field(description="Títulos com pelo menos um exemplar em circulação")
    reservations_pending: int
    reservations_hold: int
    top_books: list[TopBookItem]
