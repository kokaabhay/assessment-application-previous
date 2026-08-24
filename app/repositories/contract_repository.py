from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Contract


class ContractRepository:
    """Database operations for contracts."""

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        contract_id: int,
    ) -> Contract | None:
        """Get a contract by ID."""

        result = await db.execute(
            select(Contract).where(
                Contract.id == contract_id
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(
        db: AsyncSession,
    ) -> list[Contract]:
        """Get all contracts."""

        result = await db.execute(
            select(Contract).order_by(Contract.id)
        )

        return list(result.scalars().all())

    @staticmethod
    async def get_by_owner(
        db: AsyncSession,
        owner_id: int,
    ) -> list[Contract]:
        """Get contracts owned by a user."""

        result = await db.execute(
            select(Contract)
            .where(Contract.owner_id == owner_id)
            .order_by(Contract.id)
        )

        return list(result.scalars().all())

    @staticmethod
    async def create(
        db: AsyncSession,
        contract: Contract,
    ) -> Contract:
        """Create a contract."""

        db.add(contract)

        await db.commit()
        await db.refresh(contract)

        return contract

    @staticmethod
    async def update(
        db: AsyncSession,
        contract: Contract,
    ) -> Contract:
        """Update a contract."""

        await db.commit()
        await db.refresh(contract)

        return contract

    @staticmethod
    async def delete(
        db: AsyncSession,
        contract: Contract,
    ) -> None:
        """Delete a contract."""

        await db.delete(contract)
        await db.commit()