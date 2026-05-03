from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.author import AuthorRead


class BookCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "The Hour of the Star",
                "author_id": 1,
                "isbn": "9788535909555",
                "publication_year": 1977,
            }
        }
    )

    title: str = Field(min_length=1, max_length=500)
    author_id: int = Field(ge=1)
    description: str | None = Field(default=None, max_length=50000)
    publisher: str | None = Field(default=None, max_length=255)
    isbn: str | None = Field(default=None, max_length=32)
    publication_year: int | None = Field(default=None, ge=1000, le=3000)


class BookUpdate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "The Hour of the Star",
                "author_id": 1,
                "isbn": "9788535909555",
                "publication_year": 1977,
            }
        }
    )

    title: str | None = Field(default=None, min_length=1, max_length=500)
    author_id: int | None = Field(default=None, ge=1)
    description: str | None = Field(default=None, max_length=50000)
    publisher: str | None = Field(default=None, max_length=255)
    isbn: str | None = Field(default=None, max_length=32)
    publication_year: int | None = Field(default=None, ge=1000, le=3000)


class BookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None = None
    publisher: str | None = None
    isbn: str | None
    publication_year: int | None
    author_id: int
    author: AuthorRead
    created_at: datetime
    available: bool = Field(
        default=False,
        description="True when there is no active loan for this copy (one book row = one copy).",
    )


class BookAvailability(BaseModel):
    book_id: int
    available: bool
    reason: str | None = Field(default=None, description="Reason when unavailable.")
