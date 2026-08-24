from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Vendor


class VendorRepository:
    """Database operations related to vendors."""

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        vendor_id: int,
    ) -> Vendor | None:
        """Return a vendor by ID."""

        result = await db.execute(
            select(Vendor).where(
                Vendor.id == vendor_id
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(
        db: AsyncSession,
    ) -> list[Vendor]:
        """Return all vendors."""

        result = await db.execute(
            select(Vendor).order_by(Vendor.id)
        )

        return list(result.scalars().all())

    @staticmethod
    async def create(
        db: AsyncSession,
        vendor: Vendor,
    ) -> Vendor:
        """Persist a new vendor."""

        db.add(vendor)

        await db.commit()
        await db.refresh(vendor)

        return vendor

    @staticmethod
    async def update(
        db: AsyncSession,
        vendor: Vendor,
    ) -> Vendor:
        """Persist changes to an existing vendor."""

        await db.commit()
        await db.refresh(vendor)

        return vendor

    @staticmethod
    async def delete(
        db: AsyncSession,
        vendor: Vendor,
    ) -> None:
        """Delete a vendor."""

        await db.delete(vendor)
        await db.commit()