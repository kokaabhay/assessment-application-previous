import asyncio
import csv
import io
import json
import logging
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, require_roles
from app.core.exceptions import BusinessRuleError, ResourceNotFoundError
from app.core.cache import TTLCache
from app.db.database import AsyncSessionLocal, get_db
from app.db.models import Complaint, ComplaintCategory, ComplaintNote, Escalation, Job, User
from app.repositories.job_repository import JobRepository
from app.schemas.complaints import (
    CategoryCreate, CategoryResponse, ComplaintAssignment, ComplaintCreate,
    ComplaintResponse, ComplaintStatusUpdate, EscalationCreate, NoteCreate,
    TrendRequest, TrendResponse,
)
from app.services.complaint_service import ComplaintService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Complaints"])


def response_for(complaint: Complaint) -> ComplaintResponse:
    return ComplaintResponse.model_validate({
        **{field: getattr(complaint, field) for field in (
            "id", "customer_id", "product_id", "category", "channel", "subject",
            "description", "priority", "status", "assigned_team_id", "assigned_agent_id",
            "created_at", "sla_due_at", "resolved_at", "closed_at", "duplicate_of_id",
        )},
        "sla_state": ComplaintService.sla_state(complaint),
    })


@router.post("/complaints", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
async def create_complaint(data: ComplaintCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> ComplaintResponse:
    complaint = await ComplaintService.create(db, data, user)
    return response_for(complaint)


@router.get("/complaints", response_model=list[ComplaintResponse])
async def list_complaints(
    status_filter: str | None = Query(None, alias="status"), category: str | None = None,
    priority: str | None = None, assigned_agent_id: int | None = None,
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
) -> list[ComplaintResponse]:
    query = select(Complaint).order_by(Complaint.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    if user.role.upper() == "CUSTOMER":
        query = query.where(Complaint.customer_id == user.id)
    elif user.role.upper() == "SUPPORT_AGENT":
        query = query.where(Complaint.assigned_agent_id == user.id)
    if status_filter: query = query.where(Complaint.status == status_filter.upper())
    if category: query = query.where(Complaint.category == category)
    if priority: query = query.where(Complaint.priority == priority.upper())
    if assigned_agent_id: query = query.where(Complaint.assigned_agent_id == assigned_agent_id)
    return [response_for(item) for item in (await db.scalars(query)).all()]


@router.get("/complaints/export")
async def export_complaints(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> Response:
    complaints = list((await db.scalars(select(Complaint))).all())
    output = io.StringIO(); writer = csv.writer(output)
    writer.writerow(["id", "customer_id", "product_id", "category", "priority", "status", "created_at", "sla_due_at"])
    for item in complaints: writer.writerow([item.id, item.customer_id, item.product_id, item.category, item.priority, item.status, item.created_at.isoformat(), item.sla_due_at.isoformat()])
    return Response(output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=complaints.csv"})


@router.get("/complaints/{complaint_id}", response_model=ComplaintResponse)
async def get_complaint(complaint_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> ComplaintResponse:
    return response_for(await ComplaintService.get(db, complaint_id, user))


@router.patch("/complaints/{complaint_id}/status", response_model=ComplaintResponse)
async def update_status(complaint_id: int, data: ComplaintStatusUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> ComplaintResponse:
    complaint = await ComplaintService.get(db, complaint_id, user)
    return response_for(await ComplaintService.change_status(db, complaint, data, user))


@router.patch("/complaints/{complaint_id}/assign", response_model=ComplaintResponse)
async def assign_complaint(complaint_id: int, data: ComplaintAssignment, user: User = Depends(require_roles("ADMIN", "SUPPORT_MANAGER", "admin")), db: AsyncSession = Depends(get_db)) -> ComplaintResponse:
    complaint = await ComplaintService.get(db, complaint_id, user)
    complaint.assigned_team_id, complaint.assigned_agent_id = data.assigned_team_id, data.assigned_agent_id
    if complaint.status == "NEW": complaint.status = "ASSIGNED"
    await db.commit(); await db.refresh(complaint)
    ComplaintService.invalidate_cache()
    return response_for(complaint)


@router.post("/complaints/{complaint_id}/notes")
async def add_note(complaint_id: int, data: NoteCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> dict:
    complaint = await ComplaintService.get(db, complaint_id, user)
    ComplaintService.allowed(user, complaint, write=True)
    note = ComplaintNote(complaint_id=complaint.id, author_id=user.id, text=data.text, visibility=data.visibility)
    db.add(note); await db.commit(); await db.refresh(note)
    return {"id": note.id, "complaint_id": note.complaint_id, "text": note.text, "visibility": note.visibility}


@router.post("/complaints/{complaint_id}/escalate")
async def escalate(complaint_id: int, data: EscalationCreate, user: User = Depends(require_roles("ADMIN", "SUPPORT_MANAGER", "admin")), db: AsyncSession = Depends(get_db)) -> dict:
    complaint = await ComplaintService.get(db, complaint_id, user)
    escalation = Escalation(complaint_id=complaint.id, level=data.level, reason=data.reason, escalated_by=user.id, assigned_to=data.assigned_to)
    db.add(escalation); await db.commit(); await db.refresh(escalation)
    ComplaintService.invalidate_cache()
    return {"id": escalation.id, "complaint_id": escalation.complaint_id, "level": escalation.level, "reason": escalation.reason}


@router.post("/complaint-categories", response_model=CategoryResponse, status_code=201)
async def create_category(data: CategoryCreate, user: User = Depends(require_roles("ADMIN", "admin")), db: AsyncSession = Depends(get_db)) -> ComplaintCategory:
    category = ComplaintCategory(name=data.name, default_sla_hours=data.default_sla_hours)
    db.add(category)
    try:
        await db.commit(); await db.refresh(category)
    except Exception as exc:
        await db.rollback(); raise BusinessRuleError("Category already exists.") from exc
    return category


@router.get("/complaint-categories", response_model=list[CategoryResponse])
async def list_categories(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> list[ComplaintCategory]:
    return list((await db.scalars(select(ComplaintCategory).order_by(ComplaintCategory.name))).all())


@router.get("/analytics/support-dashboard")
async def support_dashboard(user: User = Depends(get_current_user)) -> dict:
    async def read_metrics() -> dict:
        async with AsyncSessionLocal() as db: return await ComplaintService.metrics(db, user)
    async def read_open() -> int:
        async with AsyncSessionLocal() as db: return len([c for c in (await db.scalars(select(Complaint))).all() if c.status not in {"CLOSED", "RESOLVED"}])
    async def read_escalations() -> int:
        async with AsyncSessionLocal() as db: return len((await db.scalars(select(Escalation))).all())
    metrics, open_count, escalation_count = await asyncio.gather(read_metrics(), read_open(), read_escalations())
    return {**metrics, "open_from_queue": open_count, "escalation_count": escalation_count}


@router.get("/analytics/sla-performance")
async def sla_performance(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> list[dict]:
    complaints = list((await db.scalars(select(Complaint))).all())
    groups: dict[str, list[Complaint]] = {}
    for complaint in complaints: groups.setdefault(complaint.category, []).append(complaint)
    return [{"category": category, "volume": len(items), "sla_compliance_pct": round(sum(ComplaintService.sla_state(c) != "breached" for c in items) / len(items) * 100, 2), "escalations": 0} for category, items in groups.items()]


@router.get("/analytics/agent-ranking")
async def agent_ranking(user: User = Depends(require_roles("ADMIN", "SUPPORT_MANAGER", "admin")), db: AsyncSession = Depends(get_db)) -> list[dict]:
    """Return a CTE/window-style ranking of resolved complaints by agent."""
    from sqlalchemy import case, func
    ranking = (
        select(
            Complaint.assigned_agent_id.label("agent_id"),
            func.sum(case((Complaint.status.in_(["RESOLVED", "CLOSED"]), 1), else_=0)).label("resolved_count"),
            func.rank().over(order_by=func.sum(case((Complaint.status.in_(["RESOLVED", "CLOSED"]), 1), else_=0)).desc()).label("rank"),
        ).where(Complaint.assigned_agent_id.is_not(None)).group_by(Complaint.assigned_agent_id)
    )
    return [dict(row._mapping) for row in (await db.execute(ranking)).all()]


@router.post("/ai/complaint-trend-summary", response_model=TrendResponse)
async def complaint_trend(data: TrendRequest, user: User = Depends(require_roles("ADMIN", "SUPPORT_MANAGER", "SUPPORT_AGENT", "admin")), db: AsyncSession = Depends(get_db)) -> dict:
    return await ComplaintService.trend(db, user, data.instruction)


async def process_complaint_import(job_id: int, content: bytes, customer_id: int) -> None:
    async with AsyncSessionLocal() as db:
        job = await db.get(Job, job_id)
        if not job: return
        try:
            job.status, job.started_at = "RUNNING", datetime.utcnow(); await db.commit()
            rows = list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))))
            for index, row in enumerate(rows, 1):
                try:
                    await ComplaintService.create(db, ComplaintCreate.model_validate(row), await db.get(User, customer_id))
                    job.accepted_count += 1
                except Exception as exc:
                    job.rejected_count += 1; logger.warning("Rejected complaint import row %s: %s", index, exc)
                job.progress = int(index / max(len(rows), 1) * 100); await db.commit()
            job.status, job.finished_at, job.progress = "COMPLETED", datetime.utcnow(), 100; await db.commit()
        except Exception as exc:
            job.status, job.error, job.finished_at = "FAILED", str(exc), datetime.utcnow(); await db.commit()


@router.post("/complaints/import-job", status_code=202)
async def import_job(background_tasks: BackgroundTasks, file: UploadFile = File(...), user: User = Depends(require_roles("ADMIN", "SUPPORT_MANAGER", "admin")), db: AsyncSession = Depends(get_db)) -> dict:
    job = await JobRepository.create(db, Job(job_type="complaint_import", status="PENDING", progress=0))
    background_tasks.add_task(process_complaint_import, job.id, await file.read(), user.id)
    return {"job_id": job.id, "status": job.status}

