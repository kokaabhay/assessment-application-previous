from datetime import datetime
from pydantic import BaseModel
class JobResponse(BaseModel):
    """Response containing background job status."""

    id: int
    job_type: str
    status: str
    progress: int
    started_at: datetime | None
    finished_at: datetime | None
    accepted_count: int
    rejected_count: int
    result: str | None
    error: str | None

    model_config = {
        "from_attributes": True,
    }
