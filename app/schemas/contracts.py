from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class ContractCreateRequest(BaseModel):
    """Request payload for creating a contract."""

    vendor_id: int = Field(gt=0)

    title: str = Field(
        min_length=1,
        max_length=255,
    )

    contract_value: Decimal = Field(
        gt=0,
        decimal_places=2,
    )

    spend: Decimal = Field(
        ge=0,
        decimal_places=2,
    )

    start_date: date
    end_date: date

    renewal_type: str = Field(
        min_length=1,
        max_length=50,
    )

    status: str = Field(
        min_length=1,
        max_length=50,
    )

    service_scope: str | None = Field(
        default=None,
        max_length=255,
    )


class ContractUpdateRequest(BaseModel):
    """Request payload for updating a contract."""

    vendor_id: int | None = Field(
        default=None,
        gt=0,
    )

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    contract_value: Decimal | None = Field(
        default=None,
        gt=0,
        decimal_places=2,
    )

    spend: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=2,
    )

    start_date: date | None = None
    end_date: date | None = None

    renewal_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    status: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    service_scope: str | None = Field(
        default=None,
        max_length=255,
    )


class ContractResponse(BaseModel):
    """Public contract representation."""

    id: int
    vendor_id: int
    title: str
    contract_value: Decimal
    spend: Decimal
    start_date: date
    end_date: date
    renewal_type: str
    status: str
    owner_id: int
    service_scope: str | None

    model_config = {
        "from_attributes": True,
    }