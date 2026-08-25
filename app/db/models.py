from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class User(Base):
    """Application user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    complaints: Mapped[list["Complaint"]] = relationship(
        back_populates="customer",
        foreign_keys="Complaint.customer_id",
    )


class Job(Base):
    """Tracked background job."""

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    job_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    progress: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    accepted_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    rejected_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    result: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


class SupportTeam(Base):
    """A support queue that can own complaints."""

    __tablename__ = "support_teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)


class ComplaintCategory(Base):
    """Configurable complaint category and default SLA."""

    __tablename__ = "complaint_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    default_sla_hours: Mapped[int] = mapped_column(Integer, default=48, nullable=False)


class Complaint(Base):
    """Customer complaint with deterministic workflow and SLA fields."""

    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(30), nullable=False, default="web")
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True, default="NEW")
    assigned_team_id: Mapped[int | None] = mapped_column(ForeignKey("support_teams.id"), index=True)
    assigned_agent_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    sla_due_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime)
    first_response_at: Mapped[datetime | None] = mapped_column(DateTime)
    duplicate_of_id: Mapped[int | None] = mapped_column(ForeignKey("complaints.id"), nullable=True)

    customer: Mapped["User"] = relationship(foreign_keys=[customer_id], back_populates="complaints")
    assigned_agent: Mapped["User | None"] = relationship(foreign_keys=[assigned_agent_id])
    notes: Mapped[list["ComplaintNote"]] = relationship(back_populates="complaint", cascade="all, delete-orphan")
    escalations: Mapped[list["Escalation"]] = relationship(back_populates="complaint", cascade="all, delete-orphan")


class ComplaintNote(Base):
    """Internal or customer-visible complaint timeline entry."""

    __tablename__ = "complaint_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    complaint_id: Mapped[int] = mapped_column(ForeignKey("complaints.id"), nullable=False, index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    visibility: Mapped[str] = mapped_column(String(20), nullable=False, default="customer")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    complaint: Mapped["Complaint"] = relationship(back_populates="notes")


class Escalation(Base):
    """Escalation history for a complaint."""

    __tablename__ = "escalations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    complaint_id: Mapped[int] = mapped_column(ForeignKey("complaints.id"), nullable=False, index=True)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    escalated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    escalated_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    assigned_to: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)
    complaint: Mapped["Complaint"] = relationship(back_populates="escalations")


Index("ix_complaint_filter", Complaint.customer_id, Complaint.status, Complaint.priority)
Index("ix_complaint_sla", Complaint.sla_due_at, Complaint.status)