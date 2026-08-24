from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Request payload for registering a new user."""

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )


class LoginRequest(BaseModel):
    """Request payload for authenticating a user."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Response containing an access token."""

    access_token: str
    token_type: str = "bearer"