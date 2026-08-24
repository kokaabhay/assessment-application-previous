from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.vendor_cache import vendor_cache
from app.db.models import Vendor
from app.repositories.vendor_repository import VendorRepository
from app.schemas.vendors import (
    VendorCreateRequest,
    VendorUpdateRequest,
)
from app.core.exceptions import (
    BusinessRuleError,
    ResourceNotFoundError,
)


class VendorService:
    """Business logic for vendor management."""

    @staticmethod
    async def get_vendor(
    db: AsyncSession,
    vendor_id: int,
) -> Vendor:
        """Get a vendor using the cache when available."""

        cache_key = f"vendor:{vendor_id}"

        cached_vendor = vendor_cache.get(cache_key)

        if cached_vendor is not None:
            return cached_vendor

        vendor = await VendorRepository.get_by_id(
            db,
            vendor_id,
        )

        if vendor is None:
            raise ResourceNotFoundError(
                "Vendor not found."
            )

        vendor_cache.set(
            cache_key,
            vendor,
        )

        return vendor

    @staticmethod
    async def get_vendors(
        db: AsyncSession,
    ) -> list[Vendor]:
        """Return all vendors."""

        return await VendorRepository.get_all(db)

    @staticmethod
    async def create_vendor(
        db: AsyncSession,
        data: VendorCreateRequest,
    ) -> Vendor:
        """Create a new vendor."""

        if data.annual_budget_cap < Decimal("0"):
            raise BusinessRuleError(
                "Annual budget cap cannot be negative."
            )

        vendor = Vendor(
            name=data.name,
            category=data.category,
            contact_email=str(data.contact_email),
            status=data.status,
            onboarded_at=data.onboarded_at,
            annual_budget_cap=data.annual_budget_cap,
        )

        return await VendorRepository.create(
            db,
            vendor,
        )

    @staticmethod
    async def update_vendor(
        db: AsyncSession,
        vendor_id: int,
        data: VendorUpdateRequest,
    ) -> Vendor:
        """Update an existing vendor."""

        vendor = await VendorService.get_vendor(
            db,
            vendor_id,
        )

        update_data = data.model_dump(
            exclude_unset=True
        )

        for field, value in update_data.items():
            if field == "contact_email":
                value = str(value)

            setattr(
                vendor,
                field,
                value,
            )

        updated_vendor = await VendorRepository.update(
            db,
            vendor,
        )

        # Invalidate cached vendor after update
        vendor_cache.delete(
            f"vendor:{vendor_id}"
        )

        return updated_vendor

    @staticmethod
    async def delete_vendor(
        db: AsyncSession,
        vendor_id: int,
    ) -> None:
        """Delete an existing vendor."""

        vendor = await VendorService.get_vendor(
            db,
            vendor_id,
        )

        await VendorRepository.delete(
            db,
            vendor,
        )

        # Invalidate cached vendor after deletion
        vendor_cache.delete(
            f"vendor:{vendor_id}"
        )