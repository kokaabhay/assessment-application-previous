import json
import logging
from datetime import datetime, timedelta
from typing import Any
from app.services.llm_services import LLMService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import TTLCache
from app.core.exceptions import BusinessRuleError, ForbiddenError, ResourceNotFoundError
from app.db.models import Complaint, ComplaintCategory, ComplaintNote, Escalation, User
from app.schemas.complaints import ComplaintCreate, ComplaintStatusUpdate

logger = logging.getLogger(__name__)
analytics_cache = TTLCache(ttl_seconds=60)


class ComplaintService:
    """Own complaint workflow and deterministic support rules."""

    @staticmethod
    def invalidate_cache() -> None:
        analytics_cache.clear()

    @staticmethod
    def priority(data: ComplaintCreate) -> str:
        """Calculate priority from explicit severity words, never from an LLM."""
        text = f"{data.subject} {data.description}".lower()
        if any(word in text for word in ("safety", "fraud", "outage", "critical")):
            return "CRITICAL"
        if any(word in text for word in ("urgent", "blocked", "broken", "payment","high")):
            return "HIGH"
        return data.priority.value if data.priority else "MEDIUM"

    @staticmethod
    async def create(db: AsyncSession, data: ComplaintCreate, customer: User) -> Complaint:
        category = await db.scalar(select(ComplaintCategory).where(ComplaintCategory.name == data.category))
        sla_hours = category.default_sla_hours if category else 48
        normalized = " ".join(data.subject.lower().split())
        duplicate = await db.scalar(
            select(Complaint).where(
                Complaint.customer_id == customer.id,
                Complaint.product_id == data.product_id,
                Complaint.category == data.category,
                Complaint.created_at >= datetime.utcnow() - timedelta(days=7),
            ).order_by(Complaint.created_at.desc())
        )
        if duplicate and " ".join(duplicate.subject.lower().split()) == normalized:
            raise BusinessRuleError(f"Potential duplicate complaint of #{duplicate.id}.")
        now = datetime.utcnow()
        complaint = Complaint(
            customer_id=customer.id, product_id=data.product_id, category=data.category,
            channel=data.channel, subject=data.subject, description=data.description,
            priority=ComplaintService.priority(data), status="NEW", created_at=now,
            sla_due_at=now + timedelta(hours=sla_hours), duplicate_of_id=None,
        )
        db.add(complaint)
        await db.commit()
        await db.refresh(complaint)
        ComplaintService.invalidate_cache()
        return complaint

    @staticmethod
    def allowed(user: User, complaint: Complaint, write: bool = False) -> None:
        role = user.role.upper()
        if role in {"ADMIN", "SUPPORT_MANAGER"}:
            return
        if role == "CUSTOMER" and complaint.customer_id == user.id:
            return
        if role == "SUPPORT_AGENT" and (complaint.assigned_agent_id == user.id or not write):
            return
        raise ForbiddenError("You do not have access to this complaint.")

    @staticmethod
    async def get(db: AsyncSession, complaint_id: int, user: User) -> Complaint:
        complaint = await db.get(Complaint, complaint_id)
        if complaint is None:
            raise ResourceNotFoundError("Complaint not found.")
        ComplaintService.allowed(user, complaint)
        return complaint

    @staticmethod
    async def change_status(db: AsyncSession, complaint: Complaint, update: ComplaintStatusUpdate, user: User) -> Complaint:
        role = user.role.upper()
        ComplaintService.allowed(user, complaint, write=True)
        transitions = {
            "NEW": {"ASSIGNED", "IN_PROGRESS"}, "ASSIGNED": {"IN_PROGRESS"},
            "IN_PROGRESS": {"RESOLVED"}, "RESOLVED": {"CLOSED", "REOPENED"},
            "REOPENED": {"IN_PROGRESS"}, "CLOSED": {"REOPENED"},
        }
        if update.status.value not in transitions.get(complaint.status, set()):
            raise BusinessRuleError(f"Invalid transition {complaint.status} -> {update.status.value}.")
        if role == "CUSTOMER" and update.status.value not in {"CLOSED", "REOPENED"}:
            raise ForbiddenError("Customers can only close or reopen their own complaints.")
        complaint.status = update.status.value
        if complaint.status == "RESOLVED":
            complaint.resolved_at = datetime.utcnow()
        if complaint.status == "CLOSED":
            complaint.closed_at = datetime.utcnow()
        if update.note:
            db.add(ComplaintNote(complaint_id=complaint.id, author_id=user.id, text=update.note, visibility="customer"))
        await db.commit()
        await db.refresh(complaint)
        ComplaintService.invalidate_cache()
        return complaint

    @staticmethod
    def sla_state(complaint: Complaint) -> str:
        if complaint.status in {"RESOLVED", "CLOSED"}:
            return "completed"
        remaining = (complaint.sla_due_at - datetime.utcnow()).total_seconds()
        return "breached" if remaining < 0 else "due_soon" if remaining <= 24 * 3600 else "on_track"

    @staticmethod
    async def metrics(db: AsyncSession, user: User) -> dict[str, Any]:
        key = f"dashboard:{user.id}:{user.role}"
        cached = analytics_cache.get(key)
        if cached is not None:
            return {**cached, "cache": "HIT"}
        query = select(Complaint)
        if user.role.upper() == "CUSTOMER":
            query = query.where(Complaint.customer_id == user.id)
        complaints = list((await db.scalars(query)).all())
        total = len(complaints)
        resolved = [c for c in complaints if c.resolved_at]
        breached = sum(ComplaintService.sla_state(c) == "breached" for c in complaints)
        escalated = len(list((await db.scalars(select(Escalation).join(Complaint))).all())) if complaints else 0
        result = {
            "total": total, "open": sum(c.status not in {"CLOSED", "RESOLVED"} for c in complaints),
            "by_status": {status: sum(c.status == status for c in complaints) for status in ("NEW", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "CLOSED", "REOPENED")},
            "by_category": {category: sum(c.category == category for c in complaints) for category in sorted({c.category for c in complaints})},
            "sla_compliance_pct": round((total - breached) / total * 100, 2) if total else 100.0,
            "breached": breached, "escalations": escalated,
            "avg_resolution_hours": round(sum((c.resolved_at - c.created_at).total_seconds() / 3600 for c in resolved) / len(resolved), 2) if resolved else 0,
            "cache": "MISS",
        }
        analytics_cache.set(key, result)
        return result

    @staticmethod
    async def trend(db: AsyncSession, user: User, instruction: str | None = None) -> dict[str, Any]:
        metrics = await ComplaintService.metrics(db, user)
        prompt = ("Write a concise customer-support trend narrative and 2-3 operational observations "
                  "from these computed metrics. Do not invent numbers: " + json.dumps(metrics))
        try:
            
            narrative = await LLMService().generate_text(prompt)
            observations = [line.strip(" -") for line in narrative.splitlines() if line.strip()][-3:]
        except Exception:
            logger.exception("Complaint trend LLM unavailable")
            narrative = (f"Support received {metrics['total']} complaints with "
                         f"{metrics['sla_compliance_pct']}% SLA compliance.")
            observations = [f"There are {metrics['open']} open complaints.", f"{metrics['breached']} complaints are past SLA."]
        return {"metrics": metrics, "narrative": narrative, "observations": observations}