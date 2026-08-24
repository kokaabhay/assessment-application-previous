from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_current_user,
    require_roles,
)
from app.db.database import get_db
from app.db.models import User, Vendor
from app.schemas.vendors import (
    VendorCreateRequest,
    VendorResponse,
    VendorUpdateRequest,
)
from app.services.vendor_services import VendorService


router = APIRouter(
    prefix="/vendors",
    tags=["Vendors"],
)


@router.get(
    "",
    response_model=list[VendorResponse],
)
async def list_vendors(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Vendor]:
    """Return all vendors for authenticated users."""

    return await VendorService.get_vendors(db)


@router.get(
    "/{vendor_id}",
    response_model=VendorResponse,
)
async def get_vendor(
    vendor_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Vendor:
    """Return a single vendor."""

    try:
        return await VendorService.get_vendor(
            db,
            vendor_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "",
    response_model=VendorResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_vendor(
    request: VendorCreateRequest,
    current_user: User = Depends(
        require_roles("admin")
    ),
    db: AsyncSession = Depends(get_db),
) -> Vendor:
    """Create a vendor. Admin only."""

    return await VendorService.create_vendor(
        db,
        request,
    )


@router.patch(
    "/{vendor_id}",
    response_model=VendorResponse,
)
async def update_vendor(
    vendor_id: int,
    request: VendorUpdateRequest,
    current_user: User = Depends(
        require_roles("admin")
    ),
    db: AsyncSession = Depends(get_db),
) -> Vendor:

    try:
        return await VendorService.update_vendor(
            db,
            vendor_id,
            request,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{vendor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_vendor(
    vendor_id: int,
    current_user: User = Depends(
        require_roles("admin")
    ),
    db: AsyncSession = Depends(get_db),
) -> None:

    try:
        await VendorService.delete_vendor(
            db,
            vendor_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc