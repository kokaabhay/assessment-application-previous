from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import Contract, User
from app.schemas.contracts import (
    ContractCreateRequest,
    ContractResponse,
    ContractUpdateRequest,
)
from app.services.contract_service import ContractService


router = APIRouter(
    prefix="/contracts",
    tags=["Contracts"],
)


@router.get(
    "",
    response_model=list[ContractResponse],
)
async def list_contracts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Contract]:
    """List contracts available to the current user."""

    return await ContractService.get_contracts(
        db,
        current_user,
    )


@router.get(
    "/{contract_id}",
    response_model=ContractResponse,
)
async def get_contract(
    contract_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Contract:
    """Get a single contract."""

    return await ContractService.get_contract(
        db,
        contract_id,
        current_user,
    )


@router.post(
    "",
    response_model=ContractResponse,
    status_code=201,
)
async def create_contract(
    request: ContractCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Contract:
    """Create a contract."""

    return await ContractService.create_contract(
        db,
        request,
        current_user,
    )


@router.patch(
    "/{contract_id}",
    response_model=ContractResponse,
)
async def update_contract(
    contract_id: int,
    request: ContractUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Contract:
    """Update a contract."""

    return await ContractService.update_contract(
        db,
        contract_id,
        request,
        current_user,
    )


@router.delete(
    "/{contract_id}",
    status_code=204,
)
async def delete_contract(
    contract_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a contract."""

    await ContractService.delete_contract(
        db,
        contract_id,
        current_user,
    )