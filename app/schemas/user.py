from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    """Public representation of an application user."""

    id: int
    email: EmailStr
    role: str
    category: str | None
    is_active: bool

    model_config = {
        "from_attributes": True,
    }