from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.services.fine_preview import projected_fine_if_returned_now


class LoanCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"user_id": 1, "book_id": 1}})

    user_id: int = Field(ge=1)
    book_id: int = Field(ge=1)


class LoanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    book_id: int
    renewal_count: int = 0
    borrowed_at: datetime
    due_at: datetime
    returned_at: datetime | None
    fine_amount: Decimal | None
    created_at: datetime
    book_title: str | None = Field(
        default=None,
        description="Filled when listing loans with the book relation loaded.",
    )
    author_name: str | None = Field(
        default=None,
        description="Filled when listing loans with the book relation loaded.",
    )

    @computed_field
    @property
    def is_active(self) -> bool:
        return self.returned_at is None

    @computed_field
    @property
    def is_overdue(self) -> bool:
        if self.returned_at is not None:
            return False
        due = self.due_at
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > due

    @computed_field
    @property
    def projected_fine_brl(self) -> Decimal | None:
        """Empréstimo ativo: multa estimada se devolver agora (regra dos dias corridos). Devolvido: null (use fine_amount)."""
        return projected_fine_if_returned_now(self.due_at, returned_at=self.returned_at)


class LoanReturnResult(BaseModel):
    loan: LoanRead
    fine_amount: Decimal = Field(description="Fine charged on this return (BRL).")


class LoanListFilter(str, Enum):
    active = "active"
    overdue = "overdue"
    all = "all"


class UserLoanFilter(str, Enum):
    active = "active"
    returned = "returned"
    overdue = "overdue"
    all = "all"
