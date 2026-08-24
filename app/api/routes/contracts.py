from fastapi import APIRouter, Depends,Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.llm_services import LLMService
from app.schemas.llm import ContractAnalysis
from app.core.exceptions import *
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    UploadFile,
)
from app.db.models import Contract, Job, User
from app.repositories.job_repository import JobRepository
from app.services.import_service import (
    process_contract_import,
)
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


@router.post(
    "/import",
    status_code=202,
)
async def import_contracts(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Import contracts from a CSV file."""

    if not file.filename:
        raise BusinessRuleError(
            "A file is required."
        )

    if not file.filename.lower().endswith(".csv"):
        raise BusinessRuleError(
            "Only CSV files are supported."
        )

    content = await file.read()

    job = Job(
        job_type="contract_import",
        status="queued",
        progress=0,
    )

    job = await JobRepository.create(
        db,
        job,
    )

    background_tasks.add_task(
        process_contract_import,
        job.id,
        content,
        current_user.id,
    )

    return {
        "job_id": job.id,
        "status": job.status,
    }

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

@router.post(
    "/{contract_id}/analyze",
    response_model=ContractAnalysis,
)
async def analyze_contract(
    contract_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ContractAnalysis:
    """Analyze a contract using the LLM."""

    contract = await ContractService.get_contract(
        db,
        contract_id,
        current_user,
    )

    llm_service = LLMService()

    return await llm_service.analyze_contract(
        contract
    )

@router.get("/export")
async def export_contracts(
    format: str = Query(
        default="csv",
        pattern="^(csv|json)$",
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export contracts as CSV or JSON."""

    if format == "csv":
        content = await ContractService.export_contracts_csv(
            db,
            current_user,
        )

        return Response(
            content=content,
            media_type="text/csv",
            headers={
                "Content-Disposition":
                    "attachment; filename=contracts.csv"
            },
        )

    content = await ContractService.export_contracts_json(
        db,
        current_user,
    )

    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition":
                "attachment; filename=contracts.json"
        },
    )