from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Job


class JobRepository:
    """Database operations for background jobs."""

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        job_id: int,
    ) -> Job | None:
        """Get a job by ID."""

        result = await db.execute(
            select(Job).where(Job.id == job_id)
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        job: Job,
    ) -> Job:
        """Create a job."""

        db.add(job)

        await db.commit()
        await db.refresh(job)

        return job

    @staticmethod
    async def update(
        db: AsyncSession,
        job: Job,
    ) -> Job:
        """Update a job."""

        await db.commit()
        await db.refresh(job)

        return job