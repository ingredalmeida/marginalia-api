from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"name": "Maria Silva", "email": "maria@example.com", "password": "secret123"}
        }
    )

    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"email": "maria@example.com", "password": "secret123"}}
    )

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
