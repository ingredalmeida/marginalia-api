from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    """Standard error body for domain and HTTP-style errors (4xx except 422)."""

    model_config = ConfigDict(json_schema_extra={"example": {"detail": "User not found."}})

    detail: str = Field(description="Human-readable error message.")
