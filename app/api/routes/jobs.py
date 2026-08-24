from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.exceptions import ResourceNotFoundError
from app.db.database import get_db
from app.db.models import Job, User
from app.repositories.job_repository import JobRepository
from app.schemas.job import JobResponse


router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)


@router.get(
    "/{job_id}",
    response_model=JobResponse,
)
async def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Job:
    """Get background job status."""

    job = await JobRepository.get_by_id(
        db,
        job_id,
    )

    if job is None:
        raise ResourceNotFoundError(
            "Job not found."
        )

    return job