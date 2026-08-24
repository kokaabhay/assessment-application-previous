from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


class VendorCreateRequest(BaseModel):
    """Request payload for creating a vendor."""

    name: str = Field(
        min_length=1,
        max_length=255,
    )

    category: str = Field(
        min_length=1,
        max_length=100,
    )

    contact_email: EmailStr

    status: str = Field(
        min_length=1,
        max_length=50,
    )

    onboarded_at: datetime

    annual_budget_cap: Decimal = Field(
        ge=0,
        decimal_places=2,
    )


class VendorUpdateRequest(BaseModel):
    """Request payload for updating a vendor."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    category: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    contact_email: EmailStr | None = None

    status: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    annual_budget_cap: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=2,
    )


class VendorResponse(BaseModel):
    """Public representation of a vendor."""

    id: int
    name: str
    category: str
    contact_email: EmailStr
    status: str
    onboarded_at: datetime
    annual_budget_cap: Decimal

    model_config = {
        "from_attributes": True,
    }