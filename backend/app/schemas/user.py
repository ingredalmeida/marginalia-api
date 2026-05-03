from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserUpdate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Maria Silva",
                "email": "maria.new@example.com",
                "password": "new-secret-123",
            }
        }
    )

    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    is_admin: bool = False
    created_at: datetime
